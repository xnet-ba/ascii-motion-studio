import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Settings
from engines.ascii.renderer import RenderOptions, render_ascii
from engines.image.converter import convert_image
from engines.video.converter import render_video
from engines.export.web import render_web_animation
from engines.export.zip import render_zip_package
from engines.animation.renderer import render_animation
from storage import db


@pytest.fixture
def tmp_root():
    d = Path(tempfile.mkdtemp(prefix="ams-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def make_logo_png(path: Path, size: int = 200) -> None:
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    draw.ellipse([size * 0.2, size * 0.2, size * 0.8, size * 0.8], fill="darkorange", outline="black", width=max(4, size // 25))
    draw.ellipse([size * 0.35, size * 0.35, size * 0.65, size * 0.65], fill="orange")
    img.save(path)


def make_test_video(path: Path, duration: int = 2) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"testsrc=duration={duration}:size=200x200:rate=5",
        "-pix_fmt", "yuv420p", str(path),
    ], check=True, capture_output=True, timeout=30)


def make_test_gif(path: Path, duration: int = 2) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"testsrc=duration={duration}:size=200x200:rate=5",
        "-pix_fmt", "rgb24", str(path),
    ], check=True, capture_output=True, timeout=30)


def make_test_svg(path: Path) -> None:
    path.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
        <rect width="200" height="200" fill="white"/>
        <circle cx="100" cy="100" r="70" fill="darkorange" stroke="black" stroke-width="8"/>
    </svg>''')


class TestImageConversion:
    def test_png_to_ascii_png(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "out.png"
        make_logo_png(src)
        opts = RenderOptions(width=60, mode="grayscale", background="black")
        result = convert_image(src, out, opts, output_format="png")
        assert out.exists()
        assert result["width"] == 60
        assert result["size_bytes"] > 0

    def test_png_to_ascii_gif(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "out.gif"
        make_logo_png(src)
        opts = RenderOptions(width=60, mode="color", background="black")
        result = convert_image(src, out, opts, output_format="gif")
        assert out.exists()
        assert result["size_bytes"] > 0

    def test_svg_to_ascii(self, tmp_root):
        src = tmp_root / "logo.svg"
        out = tmp_root / "out.png"
        make_test_svg(src)
        opts = RenderOptions(width=60, mode="color", background="black")
        result = convert_image(src, out, opts, output_format="png")
        assert out.exists()
        assert result["width"] == 60

    def test_transparent_background(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "out.png"
        make_logo_png(src)
        opts = RenderOptions(width=60, mode="color", background="transparent")
        result = convert_image(src, out, opts, output_format="png")
        assert out.exists()
        img = Image.open(out)
        assert img.mode == "RGBA"

    def test_black_background(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "out.png"
        make_logo_png(src)
        opts = RenderOptions(width=60, mode="color", background="black")
        result = convert_image(src, out, opts, output_format="png")
        assert out.exists()
        img = Image.open(out)
        px = img.getpixel((0, 0))
        assert px[:3] == (0, 0, 0)

    def test_color_preservation(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "out.png"
        make_logo_png(src)
        opts = RenderOptions(width=80, mode="color", background="black", contrast_adapt=False)
        result = convert_image(src, out, opts, output_format="png")
        assert out.exists()
        # Quick check that color grid is not grayscale
        img = Image.open(src)
        grid = render_ascii(img, opts)
        colors = [c for row in grid.colors for c in row]
        non_gray = sum(1 for r, g, b, a in colors if r != g or g != b)
        assert non_gray > 0

    def test_contrast_aware_logo(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "out.png"
        make_logo_png(src)
        opts = RenderOptions(width=80, mode="color", background="black", contrast_adapt=True)
        result = convert_image(src, out, opts, output_format="png")
        assert out.exists()
        img = Image.open(out)
        grid = render_ascii(img, opts)
        text = grid.to_text()
        # Logo body should be visible (non-space chars present)
        assert any(c != " " for c in text)


class TestVideoConversion:
    def test_mp4_to_ascii_gif(self, tmp_root):
        src = tmp_root / "vid.mp4"
        out = tmp_root / "out.gif"
        make_test_video(src)
        opts = RenderOptions(width=40, mode="grayscale", background="black")
        result = render_video(src, out, opts, fps=5, max_duration=2, max_frames=20, output_format="gif")
        assert out.exists()
        assert result["frames"] > 0

    def test_gif_to_ascii_gif(self, tmp_root):
        src = tmp_root / "anim.gif"
        out = tmp_root / "out.gif"
        make_test_gif(src)
        opts = RenderOptions(width=40, mode="grayscale", background="black")
        result = render_video(src, out, opts, fps=5, max_duration=2, max_frames=20, output_format="gif")
        assert out.exists()
        assert result["frames"] > 0

    def test_mp4_to_ascii_mp4(self, tmp_root):
        src = tmp_root / "vid.mp4"
        out = tmp_root / "out.mp4"
        make_test_video(src)
        opts = RenderOptions(width=40, mode="grayscale", background="black")
        result = render_video(src, out, opts, fps=5, max_duration=2, max_frames=20, output_format="mp4")
        assert out.exists()
        assert result["size_bytes"] > 0

    def test_mp4_to_ascii_webm(self, tmp_root):
        src = tmp_root / "vid.mp4"
        out = tmp_root / "out.webm"
        make_test_video(src)
        opts = RenderOptions(width=40, mode="grayscale", background="black")
        result = render_video(src, out, opts, fps=5, max_duration=2, max_frames=20, output_format="webm")
        assert out.exists()

    def test_mp4_to_ascii_mp4_with_audio(self, tmp_root):
        src = tmp_root / "vid.mp4"
        out = tmp_root / "out.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "testsrc=duration=2:size=200x200:rate=5",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
            "-pix_fmt", "yuv420p", "-shortest", str(src),
        ], check=True, capture_output=True, timeout=30)
        opts = RenderOptions(width=40, mode="grayscale", background="black")
        result = render_video(src, out, opts, fps=5, max_duration=2, max_frames=20,
                              output_format="mp4", preserve_audio=True)
        assert out.exists()
        # Verify audio stream preserved
        probe = json.loads(subprocess.run([
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_streams", str(out),
        ], check=True, capture_output=True, text=True, timeout=30).stdout)
        assert any(s.get("codec_type") == "audio" for s in probe.get("streams", []))

    def test_png_to_html_animation(self, tmp_root):
        # Treat single image as 1-frame animation via short video
        src = tmp_root / "vid.mp4"
        out = tmp_root / "anim.html"
        make_test_video(src)
        opts = RenderOptions(width=40, mode="grayscale", background="black")
        result = render_web_animation(src, out, opts, fps=5, max_duration=2, max_frames=20)
        assert out.exists()
        assert "<canvas" in out.read_text()

    def test_animation_effects_gif(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "anim.gif"
        make_logo_png(src)
        opts = RenderOptions(width=40, mode="color", background="black")
        result = render_animation(src, out, opts, fps=5, max_duration=2, max_frames=20,
                                  output_format="gif", effects=[{"name": "pulse"}])
        assert out.exists()
        assert result["frames"] > 1

    def test_zip_export(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "package.zip"
        make_logo_png(src)
        opts = RenderOptions(width=40, mode="grayscale", background="black")
        result = render_zip_package(src, out, opts, fps=5, max_duration=2, max_frames=20)
        assert out.exists()
        import zipfile
        with zipfile.ZipFile(out) as zf:
            assert "index.html" in zf.namelist()
            assert "configuration.json" in zf.namelist()
            assert "README.md" in zf.namelist()


class TestSecurityAndLimits:
    def test_invalid_file_rejection(self, tmp_root):
        src = tmp_root / "bad.exe"
        src.write_bytes(b"MZ" + b"\x00" * 100)
        from api.routes.upload import ALLOWED_TYPES, _type_from_magic
        detected = _type_from_magic(src.read_bytes(), "application/octet-stream")
        assert detected not in ALLOWED_TYPES

    def test_large_file_handling(self, tmp_root):
        from core.config import settings
        assert settings.MAX_UPLOAD_SIZE_MB > 0
        assert settings.MAX_VIDEO_DURATION_SECONDS > 0


class TestJobsAndPersistence:
    def test_concurrent_jobs_limit(self):
        from core.config import settings
        assert settings.CONCURRENT_JOBS >= 1

    def test_project_crud(self, tmp_root):
        # Override DB path for isolation
        old_db = db.DB_PATH
        db.DB_PATH = tmp_root / "test.db"
        try:
            db.init_db()
            pid = db.create_project("Test", {"width": 80}, "image", "/tmp/x.png")
            p = db.get_project(pid)
            assert p["name"] == "Test"
            assert db.delete_project(pid)
        finally:
            db.DB_PATH = old_db

    def test_job_restart_persistence(self, tmp_root):
        old_db = db.DB_PATH
        db.DB_PATH = tmp_root / "test.db"
        try:
            db.init_db()
            jid = db.create_job(None, "image_png", "/tmp/x.png")
            db.update_job(jid, status="pending")
            # Simulate restart: job remains pending and can be picked up
            j = db.get_job(jid)
            assert j["status"] == "pending"
        finally:
            db.DB_PATH = old_db

    def test_delete_old_jobs(self, tmp_root):
        old_db = db.DB_PATH
        db.DB_PATH = tmp_root / "test.db"
        try:
            db.init_db()
            old_jid = db.create_job(None, "image_png", "/tmp/x.png")
            db.update_job(old_jid, status="failed")
            new_jid = db.create_job(None, "image_png", "/tmp/x.png")
            db.update_job(new_jid, status="failed")
            cutoff = "2099-01-01T00:00:00"
            assert db.delete_old_jobs(cutoff) == 2
            assert db.get_job(old_jid) is None
            assert db.get_job(new_jid) is None
        finally:
            db.DB_PATH = old_db


class TestColorMapping:
    def test_manual_fg_color(self, tmp_root):
        src = tmp_root / "logo.png"
        out = tmp_root / "out.png"
        make_logo_png(src)
        opts = RenderOptions(width=40, mode="grayscale", background="black",
                             color_mapping="manual", fg_color=(0, 255, 0))
        grid = render_ascii(Image.open(src), opts)
        colors = [c for row in grid.colors for c in row]
        # All non-background characters should be green
        non_bg = [c for c in colors if c[3] > 0]
        assert all(c[:3] == (0, 255, 0) for c in non_bg)
