# Installation Guide

## Server requirements

- Ubuntu 24.04 LTS
- Python 3.11 or newer
- Node.js 20 or newer
- FFmpeg 6.x, FFprobe
- ImageMagick
- Nginx (via HestiaCP)
- Git

## Step-by-step

```bash
# 1. Clone repository
git clone https://github.com/xnet-ba/ascii-motion-studio.git /opt/ascii-motion-studio
cd /opt/ascii-motion-studio

# 2. Backend environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY, API_TOKEN, APP_URL

# 4. Frontend build
cd ../frontend
npm install
npm run build

# 5. Data directories
sudo mkdir -p /var/lib/ascii-motion-studio/{uploads,exports} \
             /var/log/ascii-motion-studio \
             /var/tmp/ascii-motion-studio/jobs
sudo chown -R $USER:$USER /var/lib/ascii-motion-studio \
                          /var/log/ascii-motion-studio \
                          /var/tmp/ascii-motion-studio

# 6. Systemd services
sudo cp ../deployment/ascii-motion-api.service /etc/systemd/system/
sudo cp ../deployment/ascii-motion-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ascii-motion-api ascii-motion-worker

# 7. Verify
curl http://127.0.0.1:8001/api/v1/health
```
