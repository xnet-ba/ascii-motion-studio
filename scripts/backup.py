#!/usr/bin/env python3
"""Backup ASCII Motion Studio data."""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/var/lib/ascii-motion-studio")
BACKUP_DIR = Path("/var/backups")
ENV_FILE = Path("/opt/ascii-motion-studio/backend/.env")


def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    archive = BACKUP_DIR / f"ascii-motion-{timestamp}.tar.gz"

    # Stop nothing; SQLite backup is quick and filesystem consistent enough.
    cmd = [
        "tar", "czf", str(archive),
        str(DATA_DIR),
        str(ENV_FILE),
        "/home/admin/conf/web/go.kolektiv.pro",
    ]
    subprocess.run(cmd, check=True)

    # Keep last 14 backups
    backups = sorted(BACKUP_DIR.glob("ascii-motion-*.tar.gz"))
    for old in backups[:-14]:
        old.unlink()

    print(f"Backup created: {archive}")


if __name__ == "__main__":
    main()
