import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from core.config import settings
from engines.ascii.renderer import RenderOptions
from engines.image.converter import render_grid_to_image
from storage.db import update_job


def _run(cmd: list, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          check=True)


def probe_video(path: Path) -> dict:
    cmd = [
        settings.FFPROBE_PATH,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    r = _run(cmd, timeout=30)
    return json.loads(r.stdout)


def get_video_duration(path: Path) -> float:
    info = probe_video(path)
    duration = 0.0
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            duration = max(duration, float(s.get("duration", 0) or 0))
    if duration == 0.0:
        duration = float(info.get("format", {}).get("duration", 0) or 0)
    return duration


def extract_frames(input_path: Path, out_dir: Path, fps: int,
                   max_frames: int, max_duration: int,
                   max_width: int = 960, max_height: int = 540) -> Tuple[int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = get_video_duration(input_path)
    effective_duration = min(duration, max_duration)
    total_frames = min(int(effective_duration * fps), max_frames)

    # Scale filter: preserve aspect, fit within max box
    scale_filter = f"scale='min({max_width},iw)':-1:force_original_aspect_ratio=decrease"

    cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-i", str(input_path),
        "-vf", f"fps={fps},{scale_filter}",
        "-frames:v", str(total_frames),
        "-q:v", "2",
        str(out_dir / "frame_%05d.png"),
    ]
    _run(cmd, timeout=max(60, total_frames * 2))
    return total_frames, fps


def render_video(input_path: Path, output_path: Path, options: RenderOptions,
                 fps: int = 15, max_duration: int = 20, max_frames: int = 300,
                 output_format: str = "mp4", job_id: Optional[int] = None) -> dict:
    from engines.ascii.renderer import render_ascii

    work_dir = Path(str(output_path)).parent / f"frames_{job_id or 'x'}"
    work_dir.mkdir(parents=True, exist_ok=True)

    total_frames, actual_fps = extract_frames(
        input_path, work_dir, fps, max_frames, max_duration
    )

    ascii_dir = work_dir / "ascii"
    ascii_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, total_frames + 1):
        frame_path = work_dir / f"frame_{i:05d}.png"
        if not frame_path.exists():
            break
        img = Image.open(frame_path)
        grid = render_ascii(img, options)
        out_img = render_grid_to_image(grid, options, font_size=12)
        out_img.save(ascii_dir / f"ascii_{i:05d}.png")

        if job_id and i % 5 == 0:
            update_job(job_id, progress=min(0.95, i / total_frames),
                       message=f"Processing frame {i}/{total_frames}")

    # Assemble output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "gif":
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-framerate", str(actual_fps),
            "-i", str(ascii_dir / "ascii_%05d.png"),
            "-vf", "split[s0][s1];[s0]palettegen=max_colors=64[p];[s1][p]paletteuse=dither=bayer",
            "-loop", "0",
            str(output_path),
        ]
    elif output_format == "webm":
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-framerate", str(actual_fps),
            "-i", str(ascii_dir / "ascii_%05d.png"),
            "-c:v", "libvpx-vp9",
            "-b:v", "1M",
            "-pix_fmt", "yuva420p",
            str(output_path),
        ]
    else:  # mp4
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-framerate", str(actual_fps),
            "-i", str(ascii_dir / "ascii_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path),
        ]
    _run(cmd, timeout=max(120, total_frames * 3))

    return {
        "frames": total_frames,
        "fps": actual_fps,
        "output_path": str(output_path),
        "size_bytes": output_path.stat().st_size,
    }
