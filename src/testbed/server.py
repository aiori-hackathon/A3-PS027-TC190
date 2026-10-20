"""
Controlled Testbed Server (PS-027)
Hosts a controlled test website seeded with deliberately IPv4-only and broken IPv6 assets
for rigorous ground-truth validation.
"""

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from ..config import TESTBED_PORT, TESTBED_HOST

app = FastAPI(title="AIORI PS-027 Controlled Testbed")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PS-027 Controlled Testbed Site</title>
    <!-- 1. Valid Dual-Stack Stylesheet -->
    <link rel="stylesheet" href="/static/valid-dualstack.css">
    
    <!-- 2. Seeded IPv4-Only Stylesheet (Simulated via header/path) -->
    <link rel="stylesheet" href="/mock/seeded-ipv4-only.css">
</head>
<body>
    <div class="container">
        <h1>AIORI PS-027 Controlled Testbed Site</h1>
        <p class="intro">This test environment deliberately contains both IPv6-compliant and seeded IPv4-only dependencies to verify auditor precision and recall.</p>
        
        <!-- 3. Seeded IPv4-Only Banner -->
        <div class="banner">
            <img src="/mock/seeded-ipv4-only.png" alt="Seeded IPv4 Banner" id="v4-banner">
        </div>
        
        <div id="status-box">Testing dependencies...</div>
    </div>

    <!-- 4. Valid Dual-Stack Script -->
    <script src="/static/valid-dualstack.js"></script>

    <!-- 5. Seeded IPv4-Only Script -->
    <script src="/mock/seeded-ipv4-only.js"></script>

    <!-- 6. Seeded Broken IPv6 TCP Route -->
    <script src="/mock/broken-tcp.js"></script>

    <!-- 7. Seeded Broken IPv6 TLS Handshake -->
    <script src="/mock/broken-tls.js"></script>

    <!-- 8. Seeded Broken IPv6 HTTP 500 Endpoint -->
    <script>
        fetch('/mock/broken-http-500.json')
            .then(res => console.log('Fetched mock status:', res.status))
            .catch(err => console.warn('Fetch error:', err));
    </script>
</body>
</html>
"""

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index():
    return HTML_CONTENT

@app.get("/static/valid-dualstack.css")
async def valid_css():
    css = "body { font-family: system-ui, sans-serif; background: #0b132b; color: #fff; } .container { max-width: 800px; margin: 40px auto; }"
    return Response(content=css, media_type="text/css")

@app.get("/static/valid-dualstack.js")
async def valid_js():
    js = "console.log('Valid dual-stack script loaded successfully');"
    return Response(content=js, media_type="application/javascript")

@app.get("/mock/seeded-ipv4-only.css")
async def mock_v4_css():
    css = "/* Seeded IPv4-Only CSS */ #v4-banner { border: 2px solid #ff4d4f; }"
    return Response(content=css, media_type="text/css")

@app.get("/mock/seeded-ipv4-only.js")
async def mock_v4_js():
    js = "console.log('Seeded IPv4-only script executed');"
    return Response(content=js, media_type="application/javascript")

@app.get("/mock/seeded-ipv4-only.png")
async def mock_v4_png():
    # 1x1 transparent PNG bytes
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=png_bytes, media_type="image/png")

@app.get("/mock/broken-tcp.js")
async def mock_broken_tcp():
    return Response(content="console.log('Simulated TCP response');", media_type="application/javascript")

@app.get("/mock/broken-tls.js")
async def mock_broken_tls():
    return Response(content="console.log('Simulated TLS response');", media_type="application/javascript")

@app.get("/mock/broken-http-500.json")
async def mock_broken_http():
    return JSONResponse(status_code=500, content={"error": "IPv6 Origin Gateway Failure (HTTP 500)"})

def start_testbed():
    """Starts the testbed server synchronously."""
    uvicorn.run(app, host=TESTBED_HOST, port=TESTBED_PORT, log_level="warning")

if __name__ == "__main__":
    start_testbed()
