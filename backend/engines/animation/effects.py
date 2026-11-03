import math
import random
from copy import deepcopy
from typing import List, Tuple, Optional
from engines.ascii.renderer import ASCIIGrid


def clone_grid(grid: ASCIIGrid) -> ASCIIGrid:
    return ASCIIGrid(
        width=grid.width,
        height=grid.height,
        chars=[row[:] for row in grid.chars],
        colors=[row[:] for row in grid.colors],
        cell_width=grid.cell_width,
        cell_height=grid.cell_height,
    )


def _clamp(val: float) -> float:
    return max(0.0, min(1.0, val))


def apply_pulse(grid: ASCIIGrid, frame: int, total_frames: int,
                intensity: float = 0.3, speed: float = 1.0) -> ASCIIGrid:
    g = clone_grid(grid)
    t = frame / max(1, total_frames - 1)
    factor = 1.0 + intensity * math.sin(t * math.pi * 2 * speed)
    for y in range(g.height):
        for x in range(g.width):
            r, gg, b, a = g.colors[y][x]
            g.colors[y][x] = (
                int(_clamp(r / 255.0 * factor) * 255),
                int(_clamp(gg / 255.0 * factor) * 255),
                int(_clamp(b / 255.0 * factor) * 255),
                a,
            )
    return g


def apply_flicker(grid: ASCIIGrid, frame: int, total_frames: int,
                  intensity: float = 0.4, seed: int = 42) -> ASCIIGrid:
    g = clone_grid(grid)
    rng = random.Random(seed + frame * 17)
    if rng.random() < intensity:
        dim = rng.uniform(0.3, 0.9)
        for y in range(g.height):
            for x in range(g.width):
                r, gg, b, a = g.colors[y][x]
                g.colors[y][x] = (int(r * dim), int(gg * dim), int(b * dim), a)
    return g


def apply_scan(grid: ASCIIGrid, frame: int, total_frames: int,
               intensity: float = 0.6, direction: str = "horizontal") -> ASCIIGrid:
    g = clone_grid(grid)
    t = frame / max(1, total_frames - 1)
    if direction == "horizontal":
        pos = int(t * g.width)
        width = max(1, g.width // 10)
        for y in range(g.height):
            for x in range(g.width):
                if pos <= x < pos + width:
                    r, gg, b, a = g.colors[y][x]
                    boost = 1.0 + intensity
                    g.colors[y][x] = (
                        int(_clamp(r / 255.0 * boost) * 255),
                        int(_clamp(gg / 255.0 * boost) * 255),
                        int(_clamp(b / 255.0 * boost) * 255),
                        a,
                    )
    else:
        pos = int(t * g.height)
        height = max(1, g.height // 10)
        for y in range(g.height):
            for x in range(g.width):
                if pos <= y < pos + height:
                    r, gg, b, a = g.colors[y][x]
                    boost = 1.0 + intensity
                    g.colors[y][x] = (
                        int(_clamp(r / 255.0 * boost) * 255),
                        int(_clamp(gg / 255.0 * boost) * 255),
                        int(_clamp(b / 255.0 * boost) * 255),
                        a,
                    )
    return g


def apply_glitch(grid: ASCIIGrid, frame: int, total_frames: int,
                 intensity: float = 0.2, seed: int = 42) -> ASCIIGrid:
    g = clone_grid(grid)
    rng = random.Random(seed + frame)
    if rng.random() > intensity:
        return g
    # Swap a few random rows horizontally
    for _ in range(max(1, int(g.height * intensity * 0.3))):
        y = rng.randint(0, g.height - 1)
        shift = rng.randint(1, g.width // 4)
        g.chars[y] = g.chars[y][-shift:] + g.chars[y][:-shift]
        g.colors[y] = g.colors[y][-shift:] + g.colors[y][:-shift]
    return g


def apply_matrix(grid: ASCIIGrid, frame: int, total_frames: int,
                 intensity: float = 0.8) -> ASCIIGrid:
    g = clone_grid(grid)
    for y in range(g.height):
        for x in range(g.width):
            r, gg, b, a = g.colors[y][x]
            lum = (r + gg + b) / 3.0
            g.colors[y][x] = (
                int(lum * (1.0 - intensity) * 0.2),
                int(255 * intensity + lum * (1.0 - intensity)),
                int(lum * (1.0 - intensity) * 0.2),
                a,
            )
    return g


def apply_wave(grid: ASCIIGrid, frame: int, total_frames: int,
               intensity: float = 0.3, speed: float = 2.0) -> ASCIIGrid:
    g = clone_grid(grid)
    t = frame / max(1, total_frames - 1)
    for y in range(g.height):
        offset = int(intensity * 10 * math.sin(y * 0.2 + t * math.pi * speed * 2))
        if offset == 0:
            continue
        row_chars = g.chars[y]
        row_colors = g.colors[y]
        g.chars[y] = row_chars[-offset:] + row_chars[:-offset]
        g.colors[y] = row_colors[-offset:] + row_colors[:-offset]
    return g


def apply_noise(grid: ASCIIGrid, frame: int, total_frames: int,
                intensity: float = 0.2, seed: int = 42) -> ASCIIGrid:
    g = clone_grid(grid)
    rng = random.Random(seed + frame)
    palette = " .:-=+*#%@"
    for y in range(g.height):
        for x in range(g.width):
            if rng.random() < intensity:
                g.chars[y][x] = rng.choice(palette)
                r, gg, b, a = g.colors[y][x]
                noise = rng.randint(-30, 30)
                g.colors[y][x] = (
                    max(0, min(255, r + noise)),
                    max(0, min(255, gg + noise)),
                    max(0, min(255, b + noise)),
                    a,
                )
    return g


def apply_fade_in(grid: ASCIIGrid, frame: int, total_frames: int) -> ASCIIGrid:
    g = clone_grid(grid)
    alpha = frame / max(1, total_frames - 1)
    for y in range(g.height):
        for x in range(g.width):
            r, gg, b, a = g.colors[y][x]
            g.colors[y][x] = (r, gg, b, int(a * alpha))
    return g


def apply_fade_out(grid: ASCIIGrid, frame: int, total_frames: int) -> ASCIIGrid:
    g = clone_grid(grid)
    alpha = 1.0 - frame / max(1, total_frames - 1)
    for y in range(g.height):
        for x in range(g.width):
            r, gg, b, a = g.colors[y][x]
            g.colors[y][x] = (r, gg, b, int(a * alpha))
    return g


def apply_color_shift(grid: ASCIIGrid, frame: int, total_frames: int,
                      intensity: float = 1.0) -> ASCIIGrid:
    g = clone_grid(grid)
    t = frame / max(1, total_frames - 1)
    shift = int(t * 360 * intensity)
    for y in range(g.height):
        for x in range(g.width):
            r, gg, b, a = g.colors[y][x]
            h, s, v = _rgb_to_hsv(r, gg, b)
            h = (h + shift) % 360
            nr, ng, nb = _hsv_to_rgb(h, s, v)
            g.colors[y][x] = (nr, ng, nb, a)
    return g


def apply_zoom(grid: ASCIIGrid, frame: int, total_frames: int,
               intensity: float = 0.3) -> ASCIIGrid:
    """Crop toward center to simulate zoom in/out."""
    g = clone_grid(grid)
    t = frame / max(1, total_frames - 1)
    zoom = intensity * math.sin(t * math.pi * 2)
    crop_x = int(abs(zoom) * g.width * 0.25)
    crop_y = int(abs(zoom) * g.height * 0.25)
    new_h = max(1, g.height - 2 * crop_y)
    new_w = max(1, g.width - 2 * crop_x)
    new_chars = []
    new_colors = []
    for y in range(crop_y, crop_y + new_h):
        row_c = []
        row_col = []
        for x in range(crop_x, crop_x + new_w):
            row_c.append(g.chars[y % g.height][x % g.width])
            row_col.append(g.colors[y % g.height][x % g.width])
        new_chars.append(row_c)
        new_colors.append(row_col)
    # Scale back to original size via nearest-neighbor replication
    out_chars = []
    out_colors = []
    for y in range(g.height):
        src_y = int(y * new_h / g.height)
        row_c = []
        row_col = []
        for x in range(g.width):
            src_x = int(x * new_w / g.width)
            row_c.append(new_chars[src_y][src_x])
            row_col.append(new_colors[src_y][src_x])
        out_chars.append(row_c)
        out_colors.append(row_col)
    g.chars = out_chars
    g.colors = out_colors
    return g


def apply_rotation(grid: ASCIIGrid, frame: int, total_frames: int,
                   intensity: float = 0.2) -> ASCIIGrid:
    """Simple horizontal skew to suggest rotation."""
    g = clone_grid(grid)
    t = frame / max(1, total_frames - 1)
    angle = intensity * math.sin(t * math.pi * 2) * 0.5
    for y in range(g.height):
        shift = int(angle * (y - g.height / 2))
        if shift == 0:
            continue
        g.chars[y] = g.chars[y][-shift:] + g.chars[y][:-shift]
        g.colors[y] = g.colors[y][-shift:] + g.colors[y][:-shift]
    return g


def apply_particles(grid: ASCIIGrid, frame: int, total_frames: int,
                    intensity: float = 0.2, seed: int = 42) -> ASCIIGrid:
    g = clone_grid(grid)
    rng = random.Random(seed + frame)
    count = int(intensity * 20)
    for _ in range(count):
        x = rng.randint(0, g.width - 1)
        y = rng.randint(0, g.height - 1)
        g.chars[y][x] = rng.choice(".*+")
        g.colors[y][x] = (255, 255, 255, 255)
    return g


def apply_terminal_cursor(grid: ASCIIGrid, frame: int, total_frames: int,
                          intensity: float = 0.8) -> ASCIIGrid:
    """Blinking block cursor at bottom-right."""
    g = clone_grid(grid)
    blink = (frame // max(1, total_frames // 10)) % 2 == 0
    if blink:
        g.chars[g.height - 1][g.width - 1] = "█"
        g.colors[g.height - 1][g.width - 1] = (int(255 * intensity), int(255 * intensity), int(255 * intensity), 255)
    return g


def _rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    else:
        h = (60 * ((r - g) / df) + 240) % 360
    s = 0 if mx == 0 else df / mx
    v = mx
    return h, s, v


def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


EFFECTS = {
    "pulse": apply_pulse,
    "flicker": apply_flicker,
    "scan": apply_scan,
    "glitch": apply_glitch,
    "matrix": apply_matrix,
    "wave": apply_wave,
    "noise": apply_noise,
    "fade_in": apply_fade_in,
    "fade_out": apply_fade_out,
    "color_shift": apply_color_shift,
    "zoom": apply_zoom,
    "rotation": apply_rotation,
    "particles": apply_particles,
    "terminal_cursor": apply_terminal_cursor,
}


import inspect


def apply_effects(grid: ASCIIGrid, frame: int, total_frames: int,
                  effects: List[dict]) -> ASCIIGrid:
    g = grid
    for eff in effects:
        name = eff.get("name")
        fn = EFFECTS.get(name)
        if not fn:
            continue
        sig = inspect.signature(fn)
        params = {k: v for k, v in eff.items() if k != "name" and k in sig.parameters}
        g = fn(g, frame, total_frames, **params)
    return g
