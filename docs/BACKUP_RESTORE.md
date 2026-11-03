# Backup and Restore

## What to back up

- SQLite database: `/var/lib/ascii-motion-studio/ascii_motion_studio.db`
- User uploads and exports: `/var/lib/ascii-motion-studio/`
- Environment file: `/opt/ascii-motion-studio/backend/.env`
- Hestia domain config (optional): `/home/admin/conf/web/go.kolektiv.pro/`

## Automated backup script

```bash
#!/bin/bash
DEST=/var/backups/ascii-motion-$(date +%Y%m%d-%H%M).tar.gz
tar czf "$DEST" \
  /var/lib/ascii-motion-studio \
  /opt/ascii-motion-studio/backend/.env \
  /home/admin/conf/web/go.kolektiv.pro 2>/dev/null
find /var/backups -name 'ascii-motion-*.tar.gz' -mtime +14 -delete
```

## Restore

```bash
sudo systemctl stop ascii-motion-api ascii-motion-worker
sudo tar xzf /var/backups/ascii-motion-YYYYMMDD.tar.gz -C /
sudo systemctl start ascii-motion-api ascii-motion-worker
```

After restore, rebuild the frontend if the repository version changed:
```bash
cd /opt/ascii-motion-studio/frontend && npm run build
sudo rm -rf /home/admin/web/go.kolektiv.pro/public_html/*
sudo cp -r dist/* /home/admin/web/go.kolektiv.pro/public_html/
```
