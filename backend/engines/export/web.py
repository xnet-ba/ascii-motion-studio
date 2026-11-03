import json
import base64
import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image
from core.config import settings
from engines.ascii.renderer import RenderOptions, render_ascii
from engines.video.converter import extract_frames
from engines.image.converter import render_grid_to_image
from engines.animation.effects import apply_effects


def _encode_frames(frames_dir: Path, options: RenderOptions, max_frames: int = 60,
                  effects: Optional[list] = None) -> list:
    """Encode ASCII frames into compact JSON-serializable structure."""
    encoded = []
    frame_files = sorted(frames_dir.glob("frame_*.png"))[:max_frames]
    total = len(frame_files)
    effects = effects or []
    for idx, fp in enumerate(frame_files):
        img = Image.open(fp)
        grid = render_ascii(img, options)
        if effects:
            grid = apply_effects(grid, idx, total, effects)
        # Compact: chars as string, colors as base64 rgba bytes
        chars = "\n".join("".join(row) for row in grid.chars)
        colors = []
        for row in grid.colors:
            colors.append([c[:3] for c in row])  # drop alpha for size
        encoded.append({"chars": chars, "colors": colors})
    return encoded


def render_web_animation(input_path: Path, output_path: Path, options: RenderOptions,
                         fps: int = 15, max_duration: int = 10,
                         max_frames: int = 60, effects: Optional[list] = None) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / f"web_{output_path.stem}"
    work_dir.mkdir(parents=True, exist_ok=True)

    total_frames, actual_fps = extract_frames(
        input_path, work_dir, fps, max_frames, max_duration
    )
    effects = effects or []
    frames = _encode_frames(work_dir, options, max_frames=max_frames, effects=effects)

    bg = "#000000"
    if options.background == "white":
        bg = "#ffffff"
    elif options.background == "transparent":
        bg = "transparent"

    payload = {
        "fps": actual_fps,
        "background": bg,
        "frames": frames,
    }
    # Embed JSON in HTML; moderate compression by base64
    b64 = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")

    html = f"""<!DOCTYPE html>
<html lang="bs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ASCII Motion Studio - Animacija</title>
<style>
html,body {{ margin:0; height:100%; background:{bg if bg != 'transparent' else '#111'}; overflow:hidden; display:flex; justify-content:center; align-items:center; }}
canvas {{ image-rendering: pixelated; max-width: 100%; max-height: 100%; }}
.controls {{ position:fixed; bottom:10px; left:50%; transform:translateX(-50%); display:flex; gap:8px; }}
button {{ background:#1e293b; color:#fff; border:none; padding:8px 14px; border-radius:4px; cursor:pointer; font-family:monospace; }}
button:hover {{ background:#334155; }}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="controls">
  <button id="play">Play</button>
  <button id="pause">Pause</button>
  <button id="loop">Loop: ON</button>
</div>
<script>
const data = JSON.parse(atob('{b64}'));
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const fontSize = 12;
ctx.font = `${{fontSize}}px monospace`;
const metrics = ctx.measureText('M');
const cw = metrics.width;
const ch = fontSize;
const rows = data.frames[0].chars.split('\\n');
canvas.width = rows[0].length * cw;
canvas.height = rows.length * ch;
let frameIdx = 0;
let playing = true;
let looping = true;
let last = 0;

function draw(frame) {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const lines = frame.chars.split('\\n');
  for (let y = 0; y < lines.length; y++) {{
    const line = lines[y];
    for (let x = 0; x < line.length; x++) {{
      const [r,g,b] = frame.colors[y][x];
      ctx.fillStyle = `rgb(${{r}},${{g}},${{b}})`;
      ctx.fillText(line[x], x * cw, (y + 0.85) * ch);
    }}
  }}
}}

function step(ts) {{
  if (!last) last = ts;
  const dt = ts - last;
  if (playing && dt > 1000 / data.fps) {{
    draw(data.frames[frameIdx]);
    frameIdx++;
    if (frameIdx >= data.frames.length) {{
      if (looping) frameIdx = 0; else {{ playing = false; frameIdx = data.frames.length - 1; }}
    }}
    last = ts;
  }}
  requestAnimationFrame(step);
}}
draw(data.frames[0]);
requestAnimationFrame(step);

document.getElementById('play').onclick = () => playing = true;
document.getElementById('pause').onclick = () => playing = false;
const loopBtn = document.getElementById('loop');
loopBtn.onclick = () => {{ looping = !looping; loopBtn.textContent = looping ? 'Loop: ON' : 'Loop: OFF'; }};
</script>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    return {
        "frames": len(frames),
        "fps": actual_fps,
        "output_path": str(output_path),
        "size_bytes": output_path.stat().st_size,
    }
