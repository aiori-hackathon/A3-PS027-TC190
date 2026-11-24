"""
Unified Application Launcher for PS-027 Auditor
Starts both the Controlled Testbed Server (port 8888) and the Auditor Web Dashboard (port 8000).
Gracefully terminates orphaned processes on these ports before binding.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import uvicorn

from src.testbed.server import app as testbed_app
from src.api import app as auditor_app
from src.config import API_PORT, TESTBED_PORT, API_HOST, TESTBED_HOST

def free_port(port: int):
    """Finds and terminates any stale process currently holding the target port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        pids = [p.strip() for p in result.stdout.split() if p.strip()]
        current_pid = str(os.getpid())
        for pid in pids:
            if pid != current_pid:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    time.sleep(0.2)
                except OSError:
                    pass
    except Exception:
        pass

def run_testbed():
    """Runs controlled testbed on port 8888."""
    uvicorn.run(testbed_app, host=TESTBED_HOST, port=TESTBED_PORT, log_level="warning")

def run_auditor():
    """Runs main auditor dashboard on port 8000."""
    uvicorn.run(auditor_app, host=API_HOST, port=API_PORT, log_level="info")

def main():
    # Port cleanup is a local-development convenience and is disabled by default.
    if os.environ.get("CLEAN_PORTS", "false").lower() == "true":
        free_port(API_PORT)
        free_port(TESTBED_PORT)
        time.sleep(0.3)

    print("=" * 70)
    print("  AIORI 3.0 Hackathon — Team A3-PS027-TC190")
    print("  PS-027: IPv6 Website and Dependency Readiness Auditor")
    print("=" * 70)
    testbed_enabled = os.environ.get("ENABLE_TESTBED", "true").lower() == "true"
    if testbed_enabled:
        print(f"  [1] Controlled Testbed:  http://localhost:{TESTBED_PORT}")
    print(f"  [2] Auditor Dashboard:   http://localhost:{API_PORT}")
    print(f"  [3] OpenAPI Swagger:     http://localhost:{API_PORT}/docs")
    print("=" * 70)

    if testbed_enabled:
        tb_thread = threading.Thread(target=run_testbed, daemon=True)
        tb_thread.start()
        time.sleep(0.8)

    # Launch main auditor
    run_auditor()

if __name__ == "__main__":
    main()
