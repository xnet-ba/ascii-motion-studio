# ASCII Motion Studio – Final Report

**Project:** ASCII Motion Studio  
**GitHub:** https://github.com/xnet-ba/ascii-motion-studio  
**Demo URL:** https://go.kolektiv.pro  
**Server:** K.PRO Ubuntu 24.04 (12 vCPU / 48 GB RAM / 500 GB SSD, no GPU)  
**Date:** 2026-11-03  

---

## 1. Deployed components and versions

| Component | Version / Path |
|-----------|----------------|
| Ubuntu | 24.04.5 LTS |
| Python | 3.12.3 |
| Node.js | 22.23.4 |
| PM2 | 6.0.13 |
| FFmpeg | 6.1.1 |
| FFprobe | 6.1.1 |
| ImageMagick | 6.9.12-98 |
| FastAPI | 0.115.0 |
| Pillow | 11.0.0 |
| NumPy | 2.1.2 |
| React / Vite | 18 / 6 |
| Tailwind CSS | 3.4.17 |
| HestiaCP | (existing) |
| Nginx | (existing, via Hestia) |

---

## 2. Architecture

- **Frontend:** React + TypeScript + Vite + Tailwind CSS, dark UI, Bosnian language, i18n-ready.
- **Backend:** FastAPI on `127.0.0.1:8001`, SQLite metadata/job queue, Pillow/NumPy/FFmpeg engines.
- **Worker:** Separate Python process polling SQLite for pending jobs (`CONCURRENT_JOBS=2`).
- **Web server:** HestiaCP-managed Nginx serves static build; `/api/` and `/exports/` proxy to backend.
- **Storage:** `/var/lib/ascii-motion-studio/` for uploads/exports/database, `/var/tmp/ascii-motion-studio/` for temp frames.
- **SSL:** Let's Encrypt certificate for `go.kolektiv.pro`.

---

## 3. Paths

| Purpose | Path |
|---------|------|
| Application code | `/opt/ascii-motion-studio/` |
| User data | `/var/lib/ascii-motion-studio/` |
| Logs | `/var/log/ascii-motion-studio/` |
| Temp frames | `/var/tmp/ascii-motion-studio/jobs/` |
| Frontend web root | `/home/admin/web/go.kolektiv.pro/public_html/` |
| Systemd units | `/etc/systemd/system/ascii-motion-*.service` |
| Hestia nginx template | `/usr/local/hestia/data/templates/web/nginx/ascii-motion.*` |

---

## 4. Systemd status

```
ascii-motion-api.service     active (running)
ascii-motion-worker.service  active (running)
ascii-motion-cleanup.timer   active (waiting, daily)
```

---

## 5. API status

- `GET /api/v1/health` → `{"status":"ok","app":"ASCII Motion Studio"}`
- OpenAPI docs: `https://go.kolektiv.pro/api/v1/docs`
- OpenAPI JSON: `https://go.kolektiv.pro/api/v1/openapi.json`

All endpoints require Bearer token authentication.

---

## 6. Test results

```
19 passed, 4 warnings in 15.85s
```

Tests cover:
1. PNG → ASCII → PNG
2. PNG → ASCII → GIF
3. MP4 → ASCII → GIF
4. GIF → ASCII → GIF
5. Video → HTML animation
6. SVG → ASCII
7. Transparent background
8. Black background
9. Color preservation
10. Contrast-aware logo rendering
11. Large file handling (limits)
12. Invalid file rejection
13. Concurrent jobs limit
14. Job persistence across restarts
15. Project CRUD
16. Animation effects (GIF)
17. ZIP export

---

## 7. Resource usage (idle)

| Process | CPU % | RAM % | Command |
|---------|-------|-------|---------|
| API | ~3.1% | ~0.1% | `uvicorn api.main:app` |
| Worker | ~1.9% | ~0.1% | `python workers/runner.py` |

Server memory: 47 GB total, ~39 GB available.  
Disk: 388 GB total, ~188 GB free.

---

## 8. Generated examples

Stored in `examples/` and produced during deployment testing:

- `logo-color-black.png` – color ASCII logo on black background
- `logo-color-black.gif` – same as animated GIF (1 frame)
- `video-ascii.gif` – ASCII GIF from test video
- `video-ascii.mp4` – ASCII MP4 from test video
- `animation.html` – standalone HTML/Canvas ASCII animation

---

## 9. Security report

| Control | Status |
|---------|--------|
| API authentication (Bearer token) | ✅ |
| Upload MIME + magic-byte validation | ✅ |
| File size limits | ✅ (50 MB default) |
| Video duration limits | ✅ (20 s default) |
| ASCII width / frame limits | ✅ (240 / 300) |
| Path-traversal-safe filenames | ✅ |
| FFmpeg invoked without shell | ✅ |
| No remote URL fetching | ✅ (not implemented) |
| Backend bound to localhost only | ✅ |
| HTTPS / SSL | ✅ (Let's Encrypt) |
| SQLite not exposed via web | ✅ |
| Runs as unprivileged user `sha` | ✅ |

**Risk notes:**
- API token is currently a demo token; rotate before production use.
- No rate limiting middleware is installed yet (limit enforced by Hestia/nginx only).

---

## 10. Backup procedure

```bash
sudo tar czf /var/backups/ascii-motion-$(date +%Y%m%d).tar.gz \
  /var/lib/ascii-motion-studio \
  /opt/ascii-motion-studio/backend/.env \
  /home/admin/conf/web/go.kolektiv.pro
```

Daily cleanup timer removes temp files older than 48 h and exports older than 14 days.

---

## 11. Upgrade procedure

```bash
cd /opt/ascii-motion-studio
git pull origin main
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo rm -rf /home/admin/web/go.kolektiv.pro/public_html/*
sudo cp -r dist/* /home/admin/web/go.kolektiv.pro/public_html/
sudo systemctl restart ascii-motion-api ascii-motion-worker
```

---

## 12. Known limitations / not finished

- Advanced GIF optimization (frame deduplication, disposal methods) is basic.
- Reduced-motion preference not yet enforced in HTML export.
- Worker currently shares the same SQLite file; fine for single-server load, may need queue migration if scaled horizontally.
- Zoom, rotation, particles and terminal-cursor effects are placeholders; not yet implemented.

---

## 13. Conclusion

The application meets the core completion criteria:

- ✅ Running on K.PRO server
- ✅ Image upload and ASCII generation
- ✅ Video upload and ASCII animation generation
- ✅ GIF generation with black background
- ✅ Logo contours and colors preserved
- ✅ Standalone HTML animation export
- ✅ ZIP export package
- ✅ MP4 and WebM export
- ✅ Animation effects engine (pulse, flicker, scan, glitch, matrix, wave, noise, fade_in, fade_out, color_shift)
- ✅ Project save/open API
- ✅ Documented REST API with OpenAPI
- ✅ Systemd services running and auto-restarting
- ✅ Existing K.PRO services preserved
- ✅ Test suite passing
- ✅ Code pushed to public GitHub repository
- ✅ Documentation enables re-installation
