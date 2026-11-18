from __future__ import annotations

import csv
import io
import struct
import wave
import zipfile
from pathlib import Path

import pytest

from app.core import detect, formats
from app.core.utils import (
    format_duration,
    human_size,
    sanitize_filename_suffix,
    stem_for,
    unique_path,
)
from app.engines.archive import ArchiveEngine
from app.engines.image import ImageEngine
from app.engines.table import TableEngine
from app.engines.text import TextEngine


def _pil():
    from PIL import Image

    return Image


# --------------------------------------------------------------- detection


def test_ext_helpers():
    assert formats.ext_of_path(Path("a.TAR.GZ")) == "tar.gz"
    assert formats.ext_of_path(Path("a.jpeg")) == "jpg"
    assert formats.ext_of_path(Path("a.tif")) == "tiff"
    assert formats.ext_of_path(Path("a.tgz")) == "tar.gz"
    assert formats.display("png") == "PNG"


def test_sniff_png_even_when_renamed(tmp_path):
    Image = _pil()
    path = tmp_path / "photo.jpg"
    Image.new("RGB", (16, 16), "red").save(path, format="PNG")
    assert detect.sniff_ext(path) == "png"


def test_sniff_pdf_and_zip(tmp_path):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.7\n...")
    assert detect.sniff_ext(pdf) == "pdf"

    archive = tmp_path / "data.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("a.txt", "hello")
    assert detect.sniff_ext(archive) == "zip"


def test_sniff_tar_gz(tmp_path):
    import tarfile

    archive = tmp_path / "data.tar.gz"
    source = tmp_path / "a.txt"
    source.write_text("hello", encoding="utf-8")
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(source, "a.txt")
    assert detect.sniff_ext(archive) == "tar.gz"


# ------------------------------------------------------------------ images


def test_image_png_to_webp_and_jpg(tmp_path):
    Image = _pil()
    source = tmp_path / "alpha.png"
    Image.new("RGBA", (40, 30), (255, 0, 0, 128)).save(source)
    engine = ImageEngine()

    webp = tmp_path / "out.webp"
    engine.convert(source, webp, {"quality": 80})
    assert webp.exists() and webp.stat().st_size > 0
    with Image.open(webp) as image:
        assert image.size == (40, 30)

    jpg = tmp_path / "out.jpg"
    engine.convert(source, jpg, {"quality": 70})
    with Image.open(jpg) as image:
        assert image.mode == "RGB"


def test_image_to_pdf(tmp_path):
    Image = _pil()
    source = tmp_path / "photo.png"
    Image.new("RGB", (24, 24), "blue").save(source)
    target = tmp_path / "photo.pdf"
    ImageEngine().convert(source, target, {})
    assert target.read_bytes().startswith(b"%PDF")


def test_animated_gif_to_webp(tmp_path):
    Image = _pil()
    frames = [Image.new("RGB", (20, 20), color) for color in ("red", "green", "blue")]
    source = tmp_path / "anim.gif"
    frames[0].save(
        source,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0,
    )
    target = tmp_path / "anim.webp"
    ImageEngine().convert(source, target, {"quality": 80})
    with Image.open(target) as image:
        assert getattr(image, "is_animated", False)
        assert image.n_frames == 3


def test_heic_detection_and_conversion(tmp_path):
    pillow_heif = pytest.importorskip("pillow_heif")
    Image = _pil()
    pillow_heif.register_heif_opener()
    source = tmp_path / "photo.heic"
    Image.new("RGB", (32, 24), "orange").save(source, format="HEIF")
    assert detect.sniff_ext(source) == "heic"
    target = tmp_path / "photo.png"
    ImageEngine().convert(source, target, {})
    with Image.open(target) as image:
        assert image.size == (32, 24)


# ---------------------------------------------------------------- archives


def test_archive_zip_to_tar_gz(tmp_path):
    source_dir = tmp_path / "src"
    (source_dir / "sub").mkdir(parents=True)
    (source_dir / "a.txt").write_text("hello", encoding="utf-8")
    (source_dir / "sub" / "b.txt").write_text("world", encoding="utf-8")

    archive = tmp_path / "in.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.write(source_dir / "a.txt", "a.txt")
        handle.write(source_dir / "sub" / "b.txt", "sub/b.txt")

    engine = ArchiveEngine()
    target = tmp_path / "out.tar.gz"
    engine.convert(archive, target, {})
    assert target.exists() and target.stat().st_size > 0

    import tarfile

    with tarfile.open(target, "r:gz") as handle:
        names = set(handle.getnames())
    assert {"a.txt", "sub/b.txt"} <= names


def test_archive_zip_to_7z(tmp_path):
    pytest.importorskip("py7zr")
    archive = tmp_path / "in.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("a.txt", "hello")
    target = tmp_path / "out.7z"
    ArchiveEngine().convert(archive, target, {})
    assert target.exists() and target.stat().st_size > 0


# -------------------------------------------------------------------- text


def test_markdown_to_html_and_text(tmp_path):
    source = tmp_path / "note.md"
    source.write_text("# Title\n\nHello **world**\n", encoding="utf-8")
    engine = TextEngine()

    html = tmp_path / "note.html"
    engine.convert(source, html, {})
    content = html.read_text(encoding="utf-8")
    assert "<h1>Title</h1>" in content
    assert "<strong>world</strong>" in content

    txt = tmp_path / "note.txt"
    engine.convert(source, txt, {})
    content = txt.read_text(encoding="utf-8")
    assert "Title" in content
    assert not content.startswith("note")


def test_html_to_markdown(tmp_path):
    source = tmp_path / "page.html"
    source.write_text("<h1>Title</h1><p>Hello <b>world</b></p>", encoding="utf-8")
    target = tmp_path / "page.md"
    TextEngine().convert(source, target, {})
    content = target.read_text(encoding="utf-8")
    assert "# Title" in content
    assert "**world**" in content


def test_gbk_text_file(tmp_path):
    source = tmp_path / "gbk.txt"
    source.write_bytes("中文内容".encode("gbk"))
    target = tmp_path / "gbk.html"
    TextEngine().convert(source, target, {})
    assert "中文内容" in target.read_text(encoding="utf-8")


# ------------------------------------------------------------------ tables


def test_csv_xlsx_roundtrip(tmp_path):
    engine = TableEngine()
    source = tmp_path / "data.csv"
    source.write_text("name,age\n张三,20\n李四,21\n", encoding="utf-8-sig")

    xlsx = tmp_path / "data.xlsx"
    engine.convert(source, xlsx, {})
    assert xlsx.exists()

    back = tmp_path / "back.csv"
    engine.convert(xlsx, back, {})
    rows = list(csv.reader(io.StringIO(back.read_text(encoding="utf-8-sig"))))
    assert rows[0] == ["name", "age"]
    assert rows[1] == ["张三", "20"]


# ------------------------------------------------------------------- media


def _make_wav(path: Path, seconds: float = 0.5, rate: int = 22050) -> None:
    import math

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        frames = bytearray()
        for index in range(int(rate * seconds)):
            value = int(8000 * math.sin(2 * math.pi * 440 * index / rate))
            frames += struct.pack("<h", value)
        handle.writeframes(bytes(frames))


def test_media_audio_conversion(tmp_path):
    from app.engines.media import MediaEngine

    engine = MediaEngine()
    if not engine.available():
        pytest.skip("FFmpeg not available")
    source = tmp_path / "tone.wav"
    _make_wav(source)
    target = tmp_path / "tone.mp3"
    engine.convert(source, target, {"preset": "balanced"})
    assert target.exists() and target.stat().st_size > 0


def test_media_ogg_from_low_sample_rate(tmp_path):
    from app.engines.media import MediaEngine

    engine = MediaEngine()
    if not engine.available():
        pytest.skip("FFmpeg not available")
    source = tmp_path / "low.wav"
    _make_wav(source, rate=22050)
    target = tmp_path / "low.ogg"
    engine.convert(source, target, {"preset": "balanced"})
    assert target.exists() and target.stat().st_size > 0


def test_media_video_to_gif(tmp_path):
    from app.engines import media as media_module
    from app.engines.media import MediaEngine

    engine = MediaEngine()
    ffmpeg = media_module._find_tool("ffmpeg")
    if not engine.available() or not ffmpeg:
        pytest.skip("FFmpeg not available")
    source = tmp_path / "clip.mp4"
    import subprocess

    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=320x240:rate=10",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        creationflags=media_module._CREATE_NO_WINDOW,
    )
    target = tmp_path / "clip.gif"
    engine.convert(source, target, {"preset": "small"})
    assert target.exists() and target.stat().st_size > 0


# ------------------------------------------------------------------ utils


def test_unique_path(tmp_path):
    reserved: set[str] = set()
    first = unique_path(tmp_path, "photo", "png", reserved)
    second = unique_path(tmp_path, "photo", "png", reserved)
    assert first.name == "photo.png"
    assert second.name == "photo (1).png"


def test_human_size_and_duration():
    assert human_size(512) == "512 B"
    assert human_size(2048) == "2.0 KB"
    assert human_size(5 * 1024 * 1024) == "5.0 MB"
    assert format_duration(75) == "01:15"
    assert format_duration(3675) == "1:01:15"


def test_stem_for_compound():
    assert stem_for(Path("archive.tar.gz"), "tar.gz") == "archive"
    assert stem_for(Path("photo.JPG"), "jpg") == "photo"
    assert stem_for(Path("note.md"), "md") == "note"


def test_sanitize_filename_suffix():
    assert sanitize_filename_suffix("_converted") == "_converted"
    assert sanitize_filename_suffix('a/b:c*?') == "abc"
    assert sanitize_filename_suffix("   ") == ""
    assert len(sanitize_filename_suffix("x" * 100)) == 32


def test_default_targets():
    assert formats.default_target("gif", ["webp", "png", "pdf"]) == "webp"
    assert formats.default_target("png", ["jpg", "webp"]) == "jpg"
    assert formats.default_target("mp4", ["mkv", "webm"]) == "mkv"
    assert formats.default_target("notes", []) == ""
