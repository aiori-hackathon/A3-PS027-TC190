"""
FastAPI Auditor Backend Server (PS-027)
Serves the web dashboard, REST API for live audits, benchmark datasets, testbed verification, and telemetry.
"""

import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import BASE_DIR, REPORTS_DIR, API_HOST, API_PORT
from .crawler.browser import BrowserCrawler
from .crawler.collector import DependencyGraphBuilder
from .diagnostics.pipeline import DiagnosticPipeline
from .testbed.verifier import TestbedVerifier
from .telemetry.context import TelemetryCollector
from .benchmark.runner import BenchmarkRunner

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AIORI PS-027 IPv6 Auditor",
    description="Browser-based IPv6 Website and Dependency Readiness Auditor",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
STATIC_DIR = BASE_DIR / "src" / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "src" / "web" / "templates"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Shared instances
benchmark_runner = BenchmarkRunner(headless=True)

class AuditRequest(BaseModel):
    url: str

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the primary web dashboard."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/audit")
async def perform_audit(req: AuditRequest):
    """Executes a live browser crawl and multi-stage protocol audit for the provided URL."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Target URL cannot be empty")
    
    target_spec = {
        "id": "live_audit",
        "name": url,
        "url": url,
        "sector": "Live Analysis"
    }
    try:
        import asyncio
        report = await asyncio.to_thread(benchmark_runner.audit_site, target_spec)
        return JSONResponse(content=report)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audit execution error: {str(e)}")

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

def start_api():
    """Starts the FastAPI auditor server."""
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")

if __name__ == "__main__":
    start_api()
