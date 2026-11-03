import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from core.config import settings
from storage import db
from engines.image.converter import convert_image
from engines.video.converter import render_video
from engines.export.web import render_web_animation
from engines.ascii.renderer import RenderOptions

_executor: Optional[ThreadPoolExecutor] = None
_stop_event = threading.Event()
_worker_thread: Optional[threading.Thread] = None


def _options_from_dict(opts: dict) -> RenderOptions:
    bg_color = opts.get("background_color")
    return RenderOptions(
        width=opts.get("width", 120),
        height=opts.get("height"),
        palette=opts.get("palette", "standard"),
        custom_chars=opts.get("custom_chars"),
        mode=opts.get("mode", "grayscale"),
        brightness=opts.get("brightness", 1.0),
        contrast=opts.get("contrast", 1.0),
        gamma=opts.get("gamma", 1.0),
        saturation=opts.get("saturation", 1.0),
        sharpen=opts.get("sharpen", 0.0),
        edge=opts.get("edge", False),
        denoise=opts.get("denoise", False),
        background=opts.get("background", "black"),
        background_color=tuple(bg_color) if bg_color else None,
        quantize=opts.get("quantize", 0),
        contrast_adapt=opts.get("contrast_adapt", False),
    )


def _process_job(job_id: int, job_type: str, payload: dict) -> None:
    db.update_job(job_id, status="running", progress=0.05, message="Started")
    try:
        opts = _options_from_dict(payload["options"])
        input_path = Path(payload["input_path"])
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}")

        if job_type == "image":
            output_format = payload["options"].get("output_format", "png")
            ext = output_format if output_format != "txt" else "txt"
            output_path = settings.DATA_DIR / "exports" / f"{job_id}.{ext}"
            result = convert_image(input_path, output_path, opts, output_format=output_format)
            db.update_job(job_id, status="completed", progress=1.0,
                          output_path=str(output_path),
                          result=json.dumps(result))
        elif job_type == "video":
            output_format = payload["options"].get("output_format", "gif")
            output_path = settings.DATA_DIR / "exports" / f"{job_id}.{output_format}"
            fps = payload["options"].get("fps", 15)
            max_duration = payload["options"].get("max_duration", 20)
            result = render_video(
                input_path, output_path, opts,
                fps=fps, max_duration=max_duration,
                max_frames=settings.MAX_FRAMES,
                output_format=output_format,
                job_id=job_id,
            )
            db.update_job(job_id, status="completed", progress=1.0,
                          output_path=str(output_path),
                          result=json.dumps(result))
        elif job_type == "export":
            export_type = payload["options"].get("export_type", "html")
            if export_type == "html":
                output_path = settings.DATA_DIR / "exports" / f"{job_id}.html"
                fps = payload["options"].get("fps", 15)
                max_duration = payload["options"].get("max_duration", 20)
                result = render_web_animation(
                    input_path, output_path, opts,
                    fps=fps, max_duration=max_duration,
                    max_frames=settings.MAX_FRAMES,
                )
                db.update_job(job_id, status="completed", progress=1.0,
                              output_path=str(output_path),
                              result=json.dumps(result))
            else:
                raise ValueError(f"Unsupported export type: {export_type}")
        else:
            raise ValueError(f"Unknown job type: {job_type}")
    except Exception as e:
        db.update_job(job_id, status="failed", progress=0.0, message=str(e))


def _loop() -> None:
    while not _stop_event.is_set():
        try:
            jobs = db.list_jobs(limit=1000)
            running = [j for j in jobs if j["status"] == "running"]
            if len(running) < settings.CONCURRENT_JOBS:
                pending = [j for j in jobs if j["status"] == "pending"]
                if pending:
                    job = pending[0]
                    payload_raw = job.get("result") or "{}"
                    payload = json.loads(payload_raw)
                    if payload.get("type") and payload.get("payload"):
                        # Mark as running immediately to avoid duplicate starts
                        db.update_job(job["id"], status="running", progress=0.02,
                                      message="Queued for processing")
                        _executor.submit(_process_job, job["id"], payload["type"], payload["payload"])
        except Exception:
            pass
        time.sleep(2)


def start_worker() -> None:
    global _executor, _worker_thread
    if _executor is not None:
        return
    _executor = ThreadPoolExecutor(max_workers=settings.CONCURRENT_JOBS + 1)
    _worker_thread = threading.Thread(target=_loop, daemon=True)
    _worker_thread.start()


def stop_worker() -> None:
    global _executor, _worker_thread
    _stop_event.set()
    if _worker_thread:
        _worker_thread.join(timeout=5)
    if _executor:
        _executor.shutdown(wait=False)
        _executor = None


def enqueue_job(job_id: int, job_type: str, payload: dict) -> None:
    # Store payload in result column temporarily; worker will read it.
    db.update_job(job_id, result=json.dumps({"type": job_type, "payload": payload}))
