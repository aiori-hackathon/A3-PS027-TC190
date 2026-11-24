import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

import src.api as api
from src.jobs import AuditJobStore


def test_audit_api_cache_and_trace_header():
    original_key = api.AUDIT_API_KEY
    original_runner = api.benchmark_runner.audit_site
    api.AUDIT_API_KEY = ""
    api.audit_cache.clear()
    api.audit_rate_windows.clear()
    api.benchmark_runner.audit_site = lambda target: {"url": target["url"]}
    try:
        with TestClient(api.app) as client:
            first = client.post(
                "/api/audit",
                json={"url": "https://one.one.one.one"},
                headers={"X-Request-ID": "production-test"},
            )
            second = client.post("/api/audit", json={"url": "https://one.one.one.one"})
        assert first.status_code == 200
        assert first.headers["X-Request-ID"] == "production-test"
        assert first.headers["X-Audit-Cache"] == "MISS"
        assert second.headers["X-Audit-Cache"] == "HIT"
    finally:
        api.AUDIT_API_KEY = original_key
        api.benchmark_runner.audit_site = original_runner
        api.audit_cache.clear()


def test_audit_api_key_gate():
    original_key = api.AUDIT_API_KEY
    api.AUDIT_API_KEY = "secret"
    api.audit_rate_windows.clear()
    try:
        with TestClient(api.app) as client:
            denied = client.post("/api/audit", json={"url": "https://one.one.one.one"})
        assert denied.status_code == 401
    finally:
        api.AUDIT_API_KEY = original_key


def test_job_store_persists_and_recovers_interrupted_jobs():
    with tempfile.TemporaryDirectory() as directory:
        store = AuditJobStore(Path(directory) / "jobs.sqlite3")
        job = store.create("https://example.com")
        store.set_running(job["job_id"])
        assert store.recover_interrupted() == 1
        recovered = store.get(job["job_id"])
        assert recovered["state"] == "failed"
        assert recovered["error"] == "Interrupted by process restart"
