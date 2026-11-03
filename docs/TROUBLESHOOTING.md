# Troubleshooting

## Backend will not start

Check logs:
```bash
sudo journalctl -u ascii-motion-api -n 50
sudo tail -f /var/log/ascii-motion-studio/api.log
```

Common causes:
- Port 8001 already in use: `sudo lsof -i :8001`
- Missing directories: ensure `/var/lib/ascii-motion-studio` exists and is writable.
- Invalid `.env`: verify `APP_DIR`, `DATA_DIR`, etc.

## Worker not processing jobs

```bash
sudo systemctl status ascii-motion-worker
sudo tail -f /var/log/ascii-motion-studio/worker.log
```

## Nginx returns 502

Verify backend is listening:
```bash
curl http://127.0.0.1:8001/api/v1/health
```

Check Hestia nginx config:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## SSL issues

Reissue certificate:
```bash
sudo /usr/local/hestia/bin/v-add-letsencrypt-domain admin go.kolektiv.pro
```
