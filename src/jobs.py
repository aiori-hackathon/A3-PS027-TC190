"""Durable lightweight audit job storage using SQLite."""

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


class AuditJobStore:
    def __init__(self, db_path):
        self.db_path = db_path if hasattr(db_path, "parent") else Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_jobs (
                    job_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    result_json TEXT,
                    error TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_jobs_state ON audit_jobs(state)"
            )

    def create(self, url: str) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = time.time()
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO audit_jobs(job_id, url, state, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (job_id, url, "queued", now, now),
            )
        return self.get(job_id)

    def set_running(self, job_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE audit_jobs SET state=?, updated_at=? WHERE job_id=?",
                ("running", time.time(), job_id),
            )

    def set_succeeded(self, job_id: str, result: Dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE audit_jobs SET state=?, updated_at=?, result_json=?, error=NULL WHERE job_id=?",
                ("succeeded", time.time(), json.dumps(result), job_id),
            )

    def set_failed(self, job_id: str, error: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE audit_jobs SET state=?, updated_at=?, error=? WHERE job_id=?",
                ("failed", time.time(), error[:2000], job_id),
            )

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM audit_jobs WHERE job_id=?", (job_id,)
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json")) if item.get("result_json") else None
        return item

    def recover_interrupted(self) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "UPDATE audit_jobs SET state=?, updated_at=?, error=? WHERE state IN (?, ?)",
                ("failed", time.time(), "Interrupted by process restart", "queued", "running"),
            )
            return cursor.rowcount
