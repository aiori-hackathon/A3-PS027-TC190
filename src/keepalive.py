"""
Render Free Tier Anti-Sleep Keep-Alive Service
Prevents the auditor container on Render from spinning down due to the 15-minute inactivity rule.
Sends periodic background HTTP keep-alive probes every 10 minutes.
"""

import os
import time
import logging
import threading
import requests

logger = logging.getLogger("keepalive")

_keepalive_started = False
_lock = threading.Lock()

def start_keepalive(interval_seconds: int = 600):
    """
    Launches a daemon thread that periodically pings the public or local healthcheck endpoint.
    Default interval: 600s (10 minutes), well within Render's 15-minute sleep threshold.
    """
    global _keepalive_started
    with _lock:
        if _keepalive_started:
            return
        _keepalive_started = True

    # 1. Determine target URL
    port = os.environ.get("PORT", os.environ.get("API_PORT", 8000))
    render_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("KEEP_ALIVE_URL")
    
    # If explicitly on Render or default fallback
    is_render = "RENDER" in os.environ or "RENDER_SERVICE_ID" in os.environ
    if not render_url and is_render:
        render_url = "https://a3-ps027-tc190.onrender.com"

    target_url = render_url or f"http://127.0.0.1:{port}"
    health_endpoint = f"{target_url.rstrip('/')}/api/health"

    def _loop():
        # Allow server 90 seconds to fully bind and warm up
        time.sleep(90)
        logger.info(f"KeepAlive daemon active. Target: {health_endpoint} (interval: {interval_seconds}s)")

        while True:
            try:
                t0 = time.perf_counter()
                headers = {"User-Agent": "AIORI-KeepAlive/1.0 (Render Anti-Sleep Daemon)"}
                resp = requests.get(health_endpoint, headers=headers, timeout=12)
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
                logger.info(f"KeepAlive ping successful: {resp.status_code} in {elapsed_ms}ms")
            except Exception as e:
                logger.warning(f"KeepAlive ping notice: {type(e).__name__} ({e})")

            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True, name="RenderKeepAliveWorker")
    thread.start()
