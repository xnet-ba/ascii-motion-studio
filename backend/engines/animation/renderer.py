import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image
from core.config import settings
from engines.ascii.renderer import RenderOptions, render_ascii
from engines.animation.effects import apply_effects
from engines.image.converter import render_grid_to_image
from engines.video.converter import _run


def render_animation(input_path: Path, output_path: Path, options: RenderOptions,
                     fps: int = 15, max_duration: int = 10, max_frames: int = 60,
                     output_format: str = "gif", effects: Optional[list] = None) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / f"anim_{output_path.stem}"
    work_dir.mkdir(parents=True, exist_ok=True)
    ascii_dir = work_dir / "ascii"
    ascii_dir.mkdir(parents=True, exist_ok=True)

    effects = effects or []

    # Detect if input is image or video by extension
    suffix = input_path.suffix.lower()
    video_suffixes = {".mp4", ".mov", ".webm", ".avi", ".gif"}

    if suffix in video_suffixes:
        from engines.video.converter import extract_frames
        total_frames, actual_fps = extract_frames(input_path, work_dir, fps, max_frames, max_duration)
    else:
        # Image: generate a looping animation by applying effects over N frames
        total_frames = min(max_frames, max(10, fps * max_duration))
        actual_fps = fps
        img = Image.open(input_path)
        base_grid = render_ascii(img, options)
        for i in range(1, total_frames + 1):
            grid = apply_effects(base_grid, i - 1, total_frames, effects)
            out_img = render_grid_to_image(grid, options, font_size=12)
            out_img.save(work_dir / f"frame_{i:05d}.png")

    # Render ASCII frames (apply effects for video too)
    for i in range(1, total_frames + 1):
        frame_path = work_dir / f"frame_{i:05d}.png"
        if not frame_path.exists():
            break
        img = Image.open(frame_path)
        grid = render_ascii(img, options)
        if effects:
            grid = apply_effects(grid, i - 1, total_frames, effects)
        out_img = render_grid_to_image(grid, options, font_size=12)
        out_img.save(ascii_dir / f"ascii_{i:05d}.png")

    # Assemble output
    if output_format == "gif":
        cmd = [
            settings.FFMPEG_PATH, "-y",
            "-framerate", str(actual_fps),
            "-i", str(ascii_dir / "ascii_%05d.png"),
            "-vf", "split[s0][s1];[s0]palettegen=max_colors=64[p];[s1][p]paletteuse=dither=bayer",
            "-loop", "0",
            str(output_path),
        ]
    elif output_format == "webm":
        cmd = [
            settings.FFMPEG_PATH, "-y",
            "-framerate", str(actual_fps),
            "-i", str(ascii_dir / "ascii_%05d.png"),
            "-c:v", "libvpx-vp9", "-b:v", "1M", "-pix_fmt", "yuva420p",
            str(output_path),
        ]
    else:  # mp4
        cmd = [
            settings.FFMPEG_PATH, "-y",
            "-framerate", str(actual_fps),
            "-i", str(ascii_dir / "ascii_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output_path),
        ]
    _run(cmd, timeout=max(120, total_frames * 3))

    return {
        "frames": total_frames,
        "fps": actual_fps,
        "output_path": str(output_path),
        "size_bytes": output_path.stat().st_size,
    }
