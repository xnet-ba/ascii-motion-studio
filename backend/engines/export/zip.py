import json
import zipfile
from pathlib import Path
from typing import Optional
from core.config import settings
from engines.ascii.renderer import RenderOptions
from engines.export.web import render_web_animation


def render_zip_package(input_path: Path, output_path: Path, options: RenderOptions,
                       fps: int = 15, max_duration: int = 10,
                       max_frames: int = 60, effects: Optional[list] = None) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / f"zip_{output_path.stem}"
    work_dir.mkdir(parents=True, exist_ok=True)

    html_path = work_dir / "index.html"
    render_web_animation(
        input_path, html_path, options,
        fps=fps, max_duration=max_duration,
        max_frames=max_frames, effects=effects,
    )

    config = {
        "app": settings.APP_NAME,
        "fps": fps,
        "mode": options.mode,
        "palette": options.palette,
        "background": options.background,
        "width": options.width,
    }
    config_path = work_dir / "configuration.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    readme = """# ASCII Motion Studio Export

This package contains a standalone HTML/Canvas ASCII animation.

## Usage

Open `index.html` in any modern web browser. No internet connection is required
after the file is loaded.

## Files

- `index.html` – standalone animation
- `configuration.json` – render settings
"""
    (work_dir / "README.md").write_text(readme, encoding="utf-8")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in ["index.html", "configuration.json", "README.md"]:
            zf.write(work_dir / f, arcname=f)

    return {
        "output_path": str(output_path),
        "size_bytes": output_path.stat().st_size,
    }
