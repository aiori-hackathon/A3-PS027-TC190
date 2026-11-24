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

def start_keepalive(interval_seconds: int = 240):
    """
    Launches a daemon thread that periodically pings the public or local healthcheck endpoint.
    Default interval: 240s (4 minutes), well within Render's 15-minute sleep threshold.
    """
    global _keepalive_started
    with _lock:
        if _keepalive_started:
            return
        _keepalive_started = True

    interval = int(os.environ.get("KEEPALIVE_INTERVAL_SECONDS", str(interval_seconds)))

    # 1. Determine target URL
    port = os.environ.get("PORT", os.environ.get("API_PORT", 8000))
    render_url = os.environ.get("KEEP_ALIVE_URL") or os.environ.get("RENDER_EXTERNAL_URL")
    
    # If explicitly on Render or default fallback to production domain
    is_render = "RENDER" in os.environ or "RENDER_SERVICE_ID" in os.environ or "RENDER_INSTANCE_ID" in os.environ
    if not render_url:
        render_url = "https://a3-ps027-tc190.onrender.com" if is_render else f"http://127.0.0.1:{port}"

    health_endpoint = f"{render_url.rstrip('/')}/api/health"

    def _loop():
        # Allow server 15 seconds to fully bind and warm up
        time.sleep(15)
        logger.info(f"KeepAlive daemon active. Target: {health_endpoint} (interval: {interval}s)")

        while True:
            try:
                t0 = time.perf_counter()
                headers = {"User-Agent": "AIORI-KeepAlive/1.0 (Render Anti-Sleep Daemon)"}
                resp = requests.get(health_endpoint, headers=headers, timeout=15)
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
                logger.info(f"KeepAlive ping successful: {resp.status_code} in {elapsed_ms}ms to {health_endpoint}")
            except Exception as e:
                logger.warning(f"KeepAlive ping notice: {type(e).__name__} ({e}) for {health_endpoint}")

            time.sleep(interval)

    thread = threading.Thread(target=_loop, daemon=True, name="RenderKeepAliveWorker")
    thread.start()

