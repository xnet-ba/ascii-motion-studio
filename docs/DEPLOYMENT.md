# Deployment Guide

## HestiaCP domain setup

1. Create `go.kolektiv.pro` in HestiaCP under user `admin`.
2. Enable SSL with Let's Encrypt.
3. Install the custom nginx template:
   ```bash
   sudo cp /opt/ascii-motion-studio/deployment/hestia/ascii-motion.tpl \
           /usr/local/hestia/data/templates/web/nginx/
   sudo cp /opt/ascii-motion-studio/deployment/hestia/ascii-motion.stpl \
           /usr/local/hestia/data/templates/web/nginx/
   sudo /usr/local/hestia/bin/v-change-web-domain-proxy-tpl admin go.kolektiv.pro ascii-motion
   ```
4. Deploy frontend build:
   ```bash
   sudo rm -rf /home/admin/web/go.kolektiv.pro/public_html/*
   sudo cp -r /opt/ascii-motion-studio/frontend/dist/* \
             /home/admin/web/go.kolektiv.pro/public_html/
   sudo chown -R admin:admin /home/admin/web/go.kolektiv.pro/public_html
   ```
5. Verify:
   ```bash
   curl https://go.kolektiv.pro/api/v1/health
   ```

## Reverse proxy behavior

- `/api/*` → `http://127.0.0.1:8001/api/`
- `/exports/*` → `http://127.0.0.1:8001/exports/`
- All other paths → static files in `public_html`

## Tailscale private access

The backend API is also reachable via Tailscale at `http://k-pro.taile4f320.ts.net:8001` when allowed by firewall.
