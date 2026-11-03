import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np


PALETTES = {
    "standard": " .:-=+*#%@",
    "dense": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "minimal": "  ░▒▓█",
    "blocks": " ▖▗▘▙▚▛▜▝▞▟█",
    "binary": " 01",
    "custom": " .:-=+*#%@",
}


@dataclass
class RenderOptions:
    width: int = 120
    height: Optional[int] = None
    preserve_aspect: bool = True
    palette: str = "standard"
    custom_chars: Optional[str] = None
    mode: str = "grayscale"  # grayscale, color, monochrome
    brightness: float = 1.0
    contrast: float = 1.0
    gamma: float = 1.0
    saturation: float = 1.0
    sharpen: float = 0.0
    edge: bool = False
    denoise: bool = False
    background: str = "black"  # black, white, transparent, original, custom
    background_color: Optional[Tuple[int, int, int]] = None
    quantize: int = 0
    contrast_adapt: bool = False  # logo preservation mode
    color_mapping: str = "auto"  # auto, original, manual
    fg_color: Optional[Tuple[int, int, int]] = None


def get_palette(options: RenderOptions) -> str:
    if options.palette == "custom" and options.custom_chars:
        return options.custom_chars
    return PALETTES.get(options.palette, PALETTES["standard"])


def gamma_correct(value: float, gamma: float) -> float:
    if gamma == 1.0:
        return value
    return math.pow(max(0.0, value), 1.0 / gamma)


def luminance(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def map_char(value: float, palette: str) -> str:
    value = max(0.0, min(1.0, value))
    idx = int(value * (len(palette) - 1))
    return palette[idx]


def fit_size(img_width: int, img_height: int, options: RenderOptions) -> Tuple[int, int]:
    char_aspect = 0.55  # terminal chars are taller than wide
    if options.preserve_aspect:
        target_width = options.width
        target_height = options.height or max(1, int((img_height / img_width) * target_width * char_aspect))
    else:
        target_width = options.width
        target_height = options.height or max(1, int(target_width * char_aspect))
    return max(1, target_width), max(1, target_height)


def preprocess_image(img: Image.Image, options: RenderOptions) -> Image.Image:
    # Convert to RGBA for transparent processing
    img = img.convert("RGBA")

    if options.denoise:
        img = img.filter(ImageFilter.MedianFilter(size=3))

    if options.sharpen > 0:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.0 + options.sharpen)

    if options.brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(options.brightness)

    if options.contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(options.contrast)

    if options.saturation != 1.0:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(options.saturation)

    if options.edge:
        # Edge detection on luminance, then blend back as outline.
        gray = ImageOps.grayscale(img)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        # Boost edges to white overlay
        edge_rgba = Image.merge("RGBA", (edges, edges, edges, edges))
        img = Image.alpha_composite(img, edge_rgba)

    return img


def detect_background_color(img: Image.Image) -> Tuple[int, int, int, int]:
    """Detect likely background from corners."""
    w, h = img.size
    corners = [
        img.getpixel((0, 0)),
        img.getpixel((w - 1, 0)),
        img.getpixel((0, h - 1)),
        img.getpixel((w - 1, h - 1)),
    ]
    # Return most common corner color
    return max(set(corners), key=corners.count)


def remove_background(img: Image.Image, bg_color: Optional[Tuple[int, int, int, int]] = None,
                      tolerance: int = 30) -> Image.Image:
    if bg_color is None:
        bg_color = detect_background_color(img)
    bg = bg_color[:3]
    arr = np.array(img)
    diff = np.abs(arr[:, :, :3].astype(np.int16) - np.array(bg, dtype=np.int16))
    mask = np.all(diff <= tolerance, axis=2)
    arr[mask] = [0, 0, 0, 0]
    return Image.fromarray(arr, "RGBA")


def contrast_aware_colors(img: Image.Image, bg: str = "black") -> Image.Image:
    """Preserve logo colors but adapt dark outlines for visibility on dark background."""
    arr = np.array(img.convert("RGBA"))
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3].astype(np.float32)

    # Compute luminance per pixel
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]

    if bg == "black":
        # Dark pixels on black become light gray; preserve bright/mid colors.
        dark = lum < 40
        rgb[dark] = [200, 200, 200]
    elif bg == "white":
        # Very bright pixels on white become dark gray.
        bright = lum > 220
        rgb[bright] = [50, 50, 50]

    arr[:, :, :3] = rgb.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


@dataclass
class ASCIIGrid:
    width: int
    height: int
    chars: List[List[str]]
    colors: List[List[Tuple[int, int, int, int]]]
    cell_width: int
    cell_height: int

    def to_text(self) -> str:
        return "\n".join("".join(row) for row in self.chars)

    def to_html(self, font_size: int = 12, line_height: float = 1.0) -> str:
        lines = []
        for row in self.colors:
            line_chars = []
            for r, g, b, a in row:
                color = f"rgba({r},{g},{b},{a / 255:.2f})"
                line_chars.append(f'<span style="color:{color}">█</span>')
            lines.append("".join(line_chars))
        return "<br>\n".join(lines)


def render_ascii(img: Image.Image, options: RenderOptions) -> ASCIIGrid:
    img = preprocess_image(img, options)

    # Background handling
    if options.background == "transparent":
        pass  # keep alpha
    elif options.background == "black":
        bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
        img = Image.alpha_composite(bg, img)
    elif options.background == "white":
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
    elif options.background == "custom" and options.background_color:
        bg = Image.new("RGBA", img.size, (*options.background_color, 255))
        img = Image.alpha_composite(bg, img)

    if options.contrast_adapt:
        img = contrast_aware_colors(img, bg=options.background)

    if options.quantize > 1:
        img = img.quantize(colors=options.quantize).convert("RGBA")

    target_w, target_h = fit_size(img.width, img.height, options)
    cell_w = max(1, img.width // target_w)
    cell_h = max(1, img.height // target_h)

    # Resize to exact ASCII dimensions using nearest for crisp chars
    small = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    arr = np.array(small)

    palette = get_palette(options)
    chars = []
    colors = []

    for y in range(target_h):
        row_chars = []
        row_colors = []
        for x in range(target_w):
            r, g, b, a = arr[y, x]
            lum = luminance(r, g, b)
            if options.mode == "grayscale":
                lum = gamma_correct(lum / 255.0, options.gamma)
                ch = map_char(lum, palette)
                gray = int(lum * 255)
                col = (gray, gray, gray, a)
            elif options.mode == "monochrome":
                val = 1 if lum > 127 else 0
                ch = palette[-1] if val else palette[0]
                col = (255, 255, 255, a) if val else (0, 0, 0, a)
            elif options.mode == "color":
                lum = gamma_correct(lum / 255.0, options.gamma)
                ch = map_char(lum, palette)
                col = (int(r), int(g), int(b), int(a))
            else:
                ch = " "
                col = (0, 0, 0, 0)

            if options.color_mapping == "manual" and options.fg_color:
                col = (*options.fg_color, col[3])

            row_chars.append(ch)
            row_colors.append(col)
        chars.append(row_chars)
        colors.append(row_colors)

    return ASCIIGrid(width=target_w, height=target_h, chars=chars,
                     colors=colors, cell_width=cell_w, cell_height=cell_h)
