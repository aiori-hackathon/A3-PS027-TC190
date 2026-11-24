"""
FastAPI Auditor Backend Server (PS-027)
Serves the web dashboard, REST API for live audits, benchmark datasets, testbed verification, and telemetry.
"""

import os
import json
import ipaddress
import socket
import asyncio
import time
import uuid
import hashlib
import hmac
from contextlib import asynccontextmanager
import threading
from urllib.parse import urlparse
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import (
    BASE_DIR, REPORTS_DIR, API_HOST, API_PORT, CORS_ORIGINS,
    MAX_CONCURRENT_AUDITS, AUDIT_TIMEOUT_SECONDS,
    AUDIT_CACHE_TTL_SECONDS, AUDIT_RATE_LIMIT_REQUESTS,
    AUDIT_RATE_LIMIT_WINDOW_SECONDS, MAX_AUDIT_URL_LENGTH,
    AUDIT_DB_PATH, ENABLE_KEEPALIVE, AUDIT_API_KEY,
)
from .crawler.browser import BrowserCrawler
from .crawler.collector import DependencyGraphBuilder
from .diagnostics.pipeline import DiagnosticPipeline
from .testbed.verifier import TestbedVerifier
from .telemetry.context import TelemetryCollector
from .benchmark.runner import BenchmarkRunner
from .keepalive import start_keepalive
from .jobs import AuditJobStore

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(_app):
    if ENABLE_KEEPALIVE:
        start_keepalive()
    job_store.recover_interrupted()
    yield


app = FastAPI(
    title="AIORI PS-027 IPv6 Auditor",
    description="Browser-based IPv6 Website and Dependency Readiness Auditor",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
STATIC_DIR = BASE_DIR / "src" / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "src" / "web" / "templates"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Shared instances
benchmark_runner = BenchmarkRunner(headless=True)
job_store = AuditJobStore(AUDIT_DB_PATH)
audit_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AUDITS)
job_semaphore = threading.BoundedSemaphore(MAX_CONCURRENT_AUDITS)
audit_cache = {}
audit_rate_windows = {}

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

class AuditRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=MAX_AUDIT_URL_LENGTH)


def validate_audit_url(raw_url: str) -> str:
    """Validate an audit target before passing it to the browser or network probes."""
    url = raw_url.strip()
    parsed = urlparse(url if "://" in url else f"https://{url}")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Target must be an HTTP or HTTPS URL")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="Target URLs must not contain credentials")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost") or hostname.endswith(".local"):
        raise HTTPException(status_code=400, detail="Local host targets are not allowed")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise HTTPException(status_code=400, detail="Private or non-routable target addresses are not allowed")

    try:
        port = parsed.port
    except ValueError:
        raise HTTPException(status_code=400, detail="Target URL contains an invalid port")
    if port and port not in {80, 443}:
        raise HTTPException(status_code=400, detail="Only ports 80 and 443 are allowed")

    if address is None:
        try:
            resolved = socket.getaddrinfo(hostname, port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except socket.gaierror:
            raise HTTPException(status_code=400, detail="Target hostname could not be resolved")
        if not resolved or any(not ipaddress.ip_address(item[4][0]).is_global for item in resolved):
            raise HTTPException(status_code=400, detail="Target hostname resolves to a private or non-routable address")

    return parsed.geturl()

def _audit_cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _check_audit_rate_limit(request: Request) -> None:
    if AUDIT_RATE_LIMIT_REQUESTS <= 0:
        return
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = audit_rate_windows.setdefault(client_ip, [])
    window[:] = [timestamp for timestamp in window if now - timestamp < AUDIT_RATE_LIMIT_WINDOW_SECONDS]
    if len(window) >= AUDIT_RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Audit rate limit exceeded")
    window.append(now)


def _check_audit_api_key(request: Request) -> None:
    if AUDIT_API_KEY and not hmac.compare_digest(request.headers.get("X-API-Key", ""), AUDIT_API_KEY):
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")


@app.get("/api/health")
async def health_check():
    """Returns liveness; this endpoint must remain lightweight for platform probes."""
    import datetime
    return JSONResponse(content={
        "status": "healthy",
        "service": "aiori-ps027-auditor",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "audit_capacity": MAX_CONCURRENT_AUDITS,
    })


@app.get("/api/ready")
async def readiness_check():
    """Reports whether the process can execute browser-backed audits."""
    try:
        from playwright.sync_api import sync_playwright
        browser_ready = True
    except Exception:
        browser_ready = False
    status = "ready" if browser_ready else "degraded"
    return JSONResponse(status_code=200 if browser_ready else 503, content={
        "status": status,
        "browser_runtime": browser_ready,
    })

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.head("/", include_in_schema=False)
async def serve_dashboard():
    """Serves the primary web dashboard."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/audit")
async def perform_audit(req: AuditRequest, request: Request):
    """Executes a bounded, cached live audit for a validated public target."""
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="Target URL cannot be empty")
    url = validate_audit_url(req.url)
    _check_audit_api_key(request)
    _check_audit_rate_limit(request)

    cache_key = _audit_cache_key(url)
    cached_entry = audit_cache.get(cache_key)
    if cached_entry:
        cached_at, cached_report = cached_entry
        if time.monotonic() - cached_at < AUDIT_CACHE_TTL_SECONDS:
            response = JSONResponse(content=cached_report)
            response.headers["X-Audit-Cache"] = "HIT"
            return response
        audit_cache.pop(cache_key, None)

    try:
        async with audit_semaphore:
            target_spec = {
                "id": "live_audit",
                "name": url,
                "url": url,
                "sector": "Live Analysis"
            }
            report = await asyncio.wait_for(
                asyncio.to_thread(benchmark_runner.audit_site, target_spec),
                timeout=AUDIT_TIMEOUT_SECONDS,
            )
            audit_cache[cache_key] = (time.monotonic(), report)
            response = JSONResponse(content=report)
            response.headers["X-Audit-Cache"] = "MISS"
            return response
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Audit exceeded the configured timeout")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Audit execution failed")

@app.get("/api/benchmark")
async def get_benchmark_results():
    """Returns the precomputed 30-site benchmark dataset."""
    json_path = REPORTS_DIR / "results_30_sites.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    else:
        # Generate initial benchmark sample
        payload = benchmark_runner.run_benchmark(limit=5)
        return JSONResponse(content=payload)

@app.get("/api/testbed")
async def get_testbed_verification():
    """Returns ground-truth verification of the controlled test site."""
    report = TestbedVerifier.verify()
    return JSONResponse(content=report)

@app.get("/api/telemetry")
async def get_telemetry():
    """Returns environmental client and resolver telemetry."""
    context = TelemetryCollector.get_full_context()
    return JSONResponse(content=context)

@app.get("/api/reports/csv")
async def download_csv():
    """Exports benchmark results as CSV."""
    csv_path = REPORTS_DIR / "results_30_sites.csv"
    if not csv_path.exists():
        benchmark_runner.run_benchmark(limit=5)
    return FileResponse(
        path=str(csv_path),
        filename="aiori_ps027_results_30_sites.csv",
        media_type="text/csv"
    )

@app.get("/api/reports/json")
async def download_json():
    """Exports benchmark results as JSON."""
    json_path = REPORTS_DIR / "results_30_sites.json"
    if not json_path.exists():
        benchmark_runner.run_benchmark(limit=5)
    return FileResponse(
        path=str(json_path),
        filename="aiori_ps027_results_30_sites.json",
        media_type="application/json"
    )

@app.post("/api/v2/audits", status_code=202)
async def create_audit_job(req: AuditRequest, request: Request):
    """Creates a durable audit job and starts an in-process worker."""
    url = validate_audit_url(req.url)
    _check_audit_api_key(request)
    _check_audit_rate_limit(request)
    job = job_store.create(url)

    def worker() -> None:
        acquired = job_semaphore.acquire(timeout=AUDIT_TIMEOUT_SECONDS)
        if not acquired:
            job_store.set_failed(job["job_id"], "Timed out waiting for worker capacity")
            return
        try:
            job_store.set_running(job["job_id"])
            target_spec = {"id": job["job_id"], "name": url, "url": url, "sector": "Live Analysis"}
            report = benchmark_runner.audit_site(target_spec)
            job_store.set_succeeded(job["job_id"], report)
        except Exception as exc:
            job_store.set_failed(job["job_id"], f"{type(exc).__name__}: {exc}")
        finally:
            job_semaphore.release()

    threading.Thread(target=worker, daemon=True, name="AuditJobWorker").start()
    return JSONResponse(status_code=202, content=job)


@app.get("/api/v2/audits/{job_id}")
async def get_audit_job(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit job not found")
    return JSONResponse(content=job)

def start_api():
    """Starts the FastAPI auditor server."""
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")

if __name__ == "__main__":
    start_api()
