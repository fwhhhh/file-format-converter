from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.engines import engine_for, targets_for
from app.engines.ocr import available as ocr_available
from app.engines.pandoc import find_pandoc
from app.engines.pdf import PdfEngine

PANDOC_MISSING = find_pandoc() is None


@pytest.mark.skipif(PANDOC_MISSING, reason="Pandoc is not installed")
def test_pandoc_targets_and_markdown_docx_roundtrip(tmp_path):
    assert "docx" in targets_for("md")
    assert "md" in targets_for("docx")
    assert "pdf" in targets_for("docx")

    source = tmp_path / "note.md"
    source.write_text("# 标题\n\nHello **world**\n", encoding="utf-8")
    docx = tmp_path / "note.docx"
    engine = engine_for("md", "docx")
    assert engine is not None
    engine.convert(source, docx, {"target_format": "docx", "source_format": "md"})
    with zipfile.ZipFile(docx) as archive:
        assert archive.namelist()

    back = tmp_path / "note_back.md"
    engine = engine_for("docx", "md")
    assert engine is not None
    engine.convert(docx, back, {"target_format": "md", "source_format": "docx"})
    text = back.read_text(encoding="utf-8")
    assert "标题" in text
    assert "world" in text


@pytest.mark.skipif(PANDOC_MISSING, reason="Pandoc is not installed")
def test_pandoc_gbk_text_to_docx(tmp_path):
    source = tmp_path / "gbk.txt"
    source.write_bytes("中文内容测试".encode("gbk"))
    target = tmp_path / "gbk.docx"
    engine = engine_for("txt", "docx")
    assert engine is not None
    engine.convert(source, target, {"target_format": "docx", "source_format": "txt"})
    assert target.exists() and target.stat().st_size > 0

    back = tmp_path / "gbk_back.txt"
    engine = engine_for("docx", "txt")
    assert engine is not None
    engine.convert(target, back, {"target_format": "txt", "source_format": "docx"})
    assert "中文内容测试" in back.read_text(encoding="utf-8")


def _make_scan_pdf(tmp_path):
    from PIL import Image, ImageDraw, ImageFont

    from app.engines.image import ImageEngine

    image = Image.new("RGB", (900, 260), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 84)
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 70), "SCAN TEST 123", fill="black", font=font)
    png = tmp_path / "scan.png"
    image.save(png)

    pdf = tmp_path / "scan.pdf"
    ImageEngine().convert(png, pdf, {})
    assert pdf.read_bytes().startswith(b"%PDF")
    return pdf


@pytest.mark.skipif(not ocr_available(), reason="Tesseract OCR is not available")
def test_scanned_pdf_text_extraction_uses_ocr(tmp_path):
    pdf = _make_scan_pdf(tmp_path)
    text_path = tmp_path / "scan.txt"
    PdfEngine().convert(pdf, text_path, {"target_format": "txt"})
    text = text_path.read_text(encoding="utf-8")
    assert "SCAN" in text or "123" in text


@pytest.mark.skipif(not ocr_available(), reason="Tesseract OCR is not available")
def test_scanned_pdf_to_ocr_docx(tmp_path):
    pdf = _make_scan_pdf(tmp_path)
    assert "docx_ocr" in targets_for("pdf")

    target = tmp_path / "scan_ocr.docx"
    engine = engine_for("pdf", "docx_ocr")
    assert engine is not None
    engine.convert(pdf, target, {"target_format": "docx_ocr", "source_format": "pdf"})
    with zipfile.ZipFile(target) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "SCAN" in xml or "123" in xml
