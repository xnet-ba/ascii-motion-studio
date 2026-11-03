import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from core.config import settings

DB_PATH = settings.DATA_DIR / "ascii_motion_studio.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                settings TEXT NOT NULL DEFAULT '{}',
                source_type TEXT,
                source_path TEXT
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress REAL NOT NULL DEFAULT 0,
                message TEXT,
                input_path TEXT,
                output_path TEXT,
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id);
            """
        )
        conn.commit()


def create_project(name: str, project_settings: dict, source_type: Optional[str] = None,
                   source_path: Optional[str] = None) -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO projects (name, created_at, updated_at, settings, source_type, source_path) VALUES (?, ?, ?, ?, ?, ?)",
            (name, now, now, json.dumps(project_settings), source_type, source_path)
        )
        conn.commit()
        return cur.lastrowid


def get_project(project_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            return None
        return dict(row)


def list_projects() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def delete_project(project_id: int) -> bool:
    with get_conn() as conn:
        conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cur.rowcount > 0


def create_job(project_id: Optional[int], job_type: str, input_path: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (project_id, type, status, progress, input_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, job_type, "pending", 0.0, input_path, now, now)
        )
        conn.commit()
        return cur.lastrowid


def get_job(job_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return dict(row)


def update_job(job_id: int, status: Optional[str] = None, progress: Optional[float] = None,
               message: Optional[str] = None, output_path: Optional[str] = None,
               result: Optional[str] = None) -> None:
    now = datetime.utcnow().isoformat()
    fields = ["updated_at = ?"]
    params = [now]
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if progress is not None:
        fields.append("progress = ?")
        params.append(progress)
    if message is not None:
        fields.append("message = ?")
        params.append(message)
    if output_path is not None:
        fields.append("output_path = ?")
        params.append(output_path)
    if result is not None:
        fields.append("result = ?")
        params.append(result)
    params.append(job_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()


def list_jobs(limit: int = 100, status: Optional[str] = None) -> list:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def delete_old_jobs(cutoff_iso: str, statuses: tuple = ("failed", "pending")) -> int:
    """Remove jobs with given statuses older than cutoff."""
    placeholders = ",".join("?" * len(statuses))
    with get_conn() as conn:
        cur = conn.execute(
            f"DELETE FROM jobs WHERE status IN ({placeholders}) AND created_at < ?",
            (*statuses, cutoff_iso),
        )
        conn.commit()
        return cur.rowcount
