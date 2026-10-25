# Deployment Guide: AIORI PS-027 IPv6 Readiness Auditor

This guide outlines how to deploy the **AIORI PS-027 IPv6 Website and Dependency Readiness Auditor** in production, cloud environments, or on a local server.

---

## 1. Quick Local / VPS Deployment (Bare Metal)

### Prerequisites:
- Python 3.10+ (tested on Python 3.11, 3.12, 3.14)
- Git

### Commands:
```bash
# 1. Clone repository
git clone https://github.com/aiori-hackathon/A3-PS027-TC190.git
cd A3-PS027-TC190

# 2. Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies and Playwright Chromium headless shell
pip install -r requirements.txt
playwright install --with-deps chromium

# 4. Start Unified Server
python run.py
```
- Dashboard: `http://localhost:8000`
- Controlled Testbed: `http://localhost:8888`

---

## 2. Docker & Docker Compose Deployment (Recommended for Cloud)

The repository includes a production-ready `Dockerfile` based on Microsoft's official Playwright runtime (`mcr.microsoft.com/playwright/python:v1.44.0-jammy`), ensuring all Linux graphics and headless libraries are pre-configured.

### Using Docker Compose:
```bash
docker compose up -d --build
```

### Using Plain Docker:
```bash
docker build -t aiori-ipv6-auditor .
docker run -d -p 8000:8000 -p 8888:8888 --name auditor aiori-ipv6-auditor
```

---

## 3. One-Click Cloud Platform Deployments

### Option A: Railway (Easiest)
1. Fork or push this repository to GitHub.
2. Go to [railway.app](https://railway.app), click **New Project** → **Deploy from GitHub repo**.
3. Railway automatically detects the `Dockerfile` and assigns a public URL with a dynamic `$PORT`.
4. The application reads `PORT` automatically and serves the dashboard.

### Option B: Render
1. Go to [render.com](https://render.com) → **New Web Service**.
2. Select your repository `A3-PS027-TC190`.
3. Choose **Docker** as the runtime.
4. Render automatically builds the container and maps incoming traffic to port 8000.

### Option C: Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch
fly launch
fly deploy
```

### Option D: AWS EC2 / DigitalOcean Droplet / Hetzner VPS
Run the application as a persistent systemd service:
```ini
# /etc/systemd/system/ipv6-auditor.service
[Unit]
Description=AIORI PS-027 IPv6 Auditor
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/A3-PS027-TC190
ExecStart=/home/ubuntu/A3-PS027-TC190/.venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Enable and start:
```bash
sudo systemctl enable --now ipv6-auditor
```

---

## 4. Verification After Deployment

Verify both services are healthy:
```bash
# Verify dashboard
curl -I http://<HOST>:8000/

# Verify testbed
curl -I http://<HOST>:8888/

# Verify live audit API
curl -X POST http://<HOST>:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://aiori.in"}'
```
