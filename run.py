"""
Unified Application Launcher for PS-027 Auditor
Starts both the Controlled Testbed Server (port 8888) and the Auditor Web Dashboard (port 8000).
"""

import sys
import threading
import time
import uvicorn

from src.testbed.server import app as testbed_app
from src.api import app as auditor_app
from src.config import API_PORT, TESTBED_PORT, API_HOST, TESTBED_HOST

def run_testbed():
    """Runs controlled testbed on port 8888."""
    uvicorn.run(testbed_app, host=TESTBED_HOST, port=TESTBED_PORT, log_level="warning")

def run_auditor():
    """Runs main auditor dashboard on port 8000."""
    uvicorn.run(auditor_app, host=API_HOST, port=API_PORT, log_level="info")

def main():
    print("=" * 70)
    print("  AIORI 3.0 Hackathon — Team A3-PS027-TC190")
    print("  PS-027: IPv6 Website and Dependency Readiness Auditor")
    print("=" * 70)
    print(f"  [1] Controlled Testbed:  http://localhost:{TESTBED_PORT}")
    print(f"  [2] Auditor Dashboard:   http://localhost:{API_PORT}")
    print(f"  [3] OpenAPI Swagger:     http://localhost:{API_PORT}/docs")
    print("=" * 70)

    # Launch testbed in background daemon thread
    tb_thread = threading.Thread(target=run_testbed, daemon=True)
    tb_thread.start()
    time.sleep(1.0)

    # Launch main auditor
    run_auditor()

if __name__ == "__main__":
    main()
