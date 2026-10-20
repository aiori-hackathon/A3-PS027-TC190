"""
Headless Browser Crawler Engine
Uses Playwright Chromium to instrument page execution, intercept all network calls,
and capture runtime dependencies.
"""

import time
import logging
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright, Page, Request, Response

from ..config import BROWSER_NAV_TIMEOUT, BROWSER_SETTLE_MS, DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

class BrowserCrawler:
    """Controls headless Chromium instance to extract runtime sub-resources."""

    def __init__(self, headless: bool = True):
        self.headless = headless

    def crawl(self, target_url: str) -> Dict[str, Any]:
        """
        Navigates to target_url, intercepts all network traffic, and collects loaded dependencies.
        """
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = "https://" + target_url

        parsed_target = urlparse(target_url)
        apex_domain = parsed_target.netloc.split(":")[0].lower()

        intercepted_requests: List[Dict[str, Any]] = []
        visited_urls = set()

        t0 = time.perf_counter()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1280, "height": 800},
                ignore_https_errors=True
            )

            page = context.new_page()

            # Network request listener
            def handle_request(req: Request):
                req_url = req.url
                if req_url.startswith("data:") or req_url.startswith("blob:"):
                    return

                parsed_req = urlparse(req_url)
                req_domain = parsed_req.netloc.split(":")[0].lower()
                is_first_party = (
                    req_domain == apex_domain or
                    req_domain.endswith("." + apex_domain)
                )

                # Capture request metadata
                record = {
                    "id": f"res_{len(intercepted_requests) + 1}",
                    "url": req_url,
                    "domain": req_domain,
                    "scheme": parsed_req.scheme,
                    "method": req.method,
                    "resource_type": req.resource_type,
                    "is_first_party": is_first_party,
                    "timestamp": time.time(),
                    "status_code": None,
                    "content_length": None,
                    "content_type": None,
                    "error": None
                }
                intercepted_requests.append(record)

            # Response listener to update status
            def handle_response(res: Response):
                req_url = res.url
                for item in reversed(intercepted_requests):
                    if item["url"] == req_url and item["status_code"] is None:
                        item["status_code"] = res.status
                        headers = res.headers
                        item["content_type"] = headers.get("content-type")
                        length = headers.get("content-length")
                        if length and length.isdigit():
                            item["content_length"] = int(length)
                        break

            # Request failed listener
            def handle_request_failed(req: Request):
                req_url = req.url
                for item in reversed(intercepted_requests):
                    if item["url"] == req_url and item["status_code"] is None:
                        item["error"] = req.failure
                        break

            page.on("request", handle_request)
            page.on("response", handle_response)
            page.on("requestfailed", handle_request_failed)

            # Navigate to page
            page_title = None
            nav_success = False
            error_msg = None

            try:
                response = page.goto(
                    target_url,
                    wait_until="domcontentloaded",
                    timeout=BROWSER_NAV_TIMEOUT
                )
                page_title = page.title()
                nav_success = True
                
                # Allow dynamic asynchronous scripts/images to fire
                page.wait_for_timeout(BROWSER_SETTLE_MS)

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Browser navigation warning for {target_url}: {e}")
            finally:
                browser.close()

        total_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "target_url": target_url,
            "apex_domain": apex_domain,
            "page_title": page_title,
            "navigation_success": nav_success,
            "navigation_error": error_msg,
            "total_crawl_time_ms": total_time_ms,
            "requests": intercepted_requests
        }
