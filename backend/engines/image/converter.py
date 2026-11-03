import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from core.config import settings
from engines.ascii.renderer import RenderOptions, render_ascii, ASCIIGrid


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Best-effort monospace font."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_grid_to_image(grid: ASCIIGrid, options: RenderOptions,
                         font_size: int = 12) -> Image.Image:
    font = _get_font(font_size)
    # Estimate char size
    bbox = font.getbbox("M")
    cw = bbox[2] - bbox[0] if bbox else font_size * 0.6
    cell_h = bbox[3] - bbox[1] if bbox else font_size

    img_w = int(grid.width * cw + 10)
    img_h = int(grid.height * cell_h + 10)

    # Background
    if options.background == "transparent":
        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    elif options.background == "white":
        img = Image.new("RGBA", (img_w, img_h), (255, 255, 255, 255))
    elif options.background == "custom" and options.background_color:
        img = Image.new("RGBA", (img_w, img_h), (*options.background_color, 255))
    else:
        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 255))

    draw = ImageDraw.Draw(img)
    for y, row in enumerate(grid.chars):
        for x, char in enumerate(row):
            r, g, b, a = grid.colors[y][x]
            if a == 0:
                continue
            draw.text((int(x * cw + 5), int(y * cell_h + 5)), char,
                      fill=(r, g, b, a), font=font)
    return img


def _load_source(input_path: Path) -> Image.Image:
    if input_path.suffix.lower() == ".svg":
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            subprocess.run([
                settings.IMAGEMAGICK_CONVERT_PATH,
                str(input_path), "-background", "none", "-resize", "1200x1200>",
                tmp.name,
            ], check=True, capture_output=True, timeout=30)
            return Image.open(tmp.name)
    return Image.open(input_path)


def convert_image(input_path: Path, output_path: Path, options: RenderOptions,
                  output_format: str = "png", font_size: int = 12) -> dict:
    img = _load_source(input_path)
    grid = render_ascii(img, options)

    result = {
        "width": grid.width,
        "height": grid.height,
        "text": grid.to_text(),
        "output_path": str(output_path),
    }

    if output_format in ("png", "jpg", "jpeg", "webp", "gif"):
        out_img = render_grid_to_image(grid, options, font_size=font_size)
        if output_format == "gif":
            # Convert to palette for smaller GIF; transparency if requested
            alpha = out_img.split()[-1] if out_img.mode == "RGBA" else None
            if options.background == "transparent" and alpha:
                mask = alpha.point(lambda a: 255 if a > 0 else 0, mode="1")
                out_img = out_img.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=64)
                out_img.save(output_path, transparency=0, optimize=True)
            else:
                out_img = out_img.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=64)
                out_img.save(output_path, optimize=True)
        else:
            out_img.save(output_path)
    elif output_format == "svg":
        output_path.write_text(_grid_to_svg(grid, options))
    elif output_format == "txt":
        output_path.write_text(grid.to_text())
    elif output_format == "html":
        output_path.write_text(_grid_to_html(grid, options))
    else:
        raise ValueError(f"Unsupported format: {output_format}")

    result["size_bytes"] = output_path.stat().st_size
    return result


def _grid_to_html(grid: ASCIIGrid, options: RenderOptions) -> str:
    bg = "transparent"
    if options.background == "black":
        bg = "#000000"
    elif options.background == "white":
        bg = "#ffffff"
    elif options.background == "custom" and options.background_color:
        bg = f"rgb({options.background_color[0]},{options.background_color[1]},{options.background_color[2]})"

    lines = []
    for row in grid.colors:
        line = []
        for r, g, b, a in row:
            line.append(f'<span style="color:rgba({r},{g},{b},{a / 255:.2f})">█</span>')
        lines.append("".join(line))
    content = "<br>".join(lines)

    return f"""<!DOCTYPE html>
<html lang="bs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ASCII Motion Studio</title>
<style>
body {{ margin:0; background:{bg}; color:#fff; font-family:monospace; display:flex; justify-content:center; align-items:center; min-height:100vh; }}
pre {{ font-size:10px; line-height:10px; letter-spacing:0; }}
</style>
</head>
<body>
<pre>{content}</pre>
</body>
</html>"""


def _grid_to_svg(grid: ASCIIGrid, options: RenderOptions) -> str:
    char_w = 8
    char_h = 14
    w = grid.width * char_w
    h = grid.height * char_h
    bg = "transparent"
    if options.background == "black":
        bg = "rgb(0,0,0)"
    elif options.background == "white":
        bg = "rgb(255,255,255)"
    elif options.background == "custom" and options.background_color:
        bg = f"rgb({options.background_color[0]},{options.background_color[1]},{options.background_color[2]})"

    rects = []
    for y, row in enumerate(grid.colors):
        for x, (r, g, b, a) in enumerate(row):
            if a == 0:
                continue
            rects.append(f'<rect x="{x * char_w}" y="{y * char_h}" width="{char_w}" height="{char_h}" '
                         f'fill="rgba({r},{g},{b},{a / 255:.2f})"/>')

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" style="background:{bg};">
{''.join(rects)}
</svg>"""
