from __future__ import annotations

import pytest

from app.engines.calibre import CalibreEngine, find_ebook_convert
from app.engines.libreoffice import LibreOfficeEngine, find_soffice
from app.engines.pandoc import find_pandoc

SOFFICE_MISSING = find_soffice() is None
CALIBRE_MISSING = find_ebook_convert() is None
PANDOC_MISSING = find_pandoc() is None


@pytest.mark.skipif(SOFFICE_MISSING, reason="LibreOffice is not installed")
def test_libreoffice_docx_to_pdf(tmp_path):
    from app.main import _write_minimal_docx

    source = tmp_path / "sample.docx"
    _write_minimal_docx(source)
    target = tmp_path / "sample.pdf"
    LibreOfficeEngine().convert(
        source, target, {"target_format": "pdf", "source_format": "docx"}
    )
    assert target.read_bytes().startswith(b"%PDF")


@pytest.mark.skipif(SOFFICE_MISSING, reason="LibreOffice is not installed")
def test_libreoffice_xlsx_to_pdf(tmp_path):
    from openpyxl import Workbook

    source = tmp_path / "sample.xlsx"
    workbook = Workbook()
    workbook.active.append(["name", "value"])
    workbook.active.append(["hello", 1])
    workbook.save(source)
    target = tmp_path / "sample.pdf"
    LibreOfficeEngine().convert(
        source, target, {"target_format": "pdf", "source_format": "xlsx"}
    )
    assert target.read_bytes().startswith(b"%PDF")


@pytest.mark.skipif(
    CALIBRE_MISSING or PANDOC_MISSING,
    reason="Calibre or Pandoc is not installed",
)
def test_calibre_epub_to_mobi(tmp_path):
    from app.engines import engine_for

    markdown = tmp_path / "book.md"
    markdown.write_text("# Chapter\n\nHello e-book.\n", encoding="utf-8")
    epub = tmp_path / "book.epub"
    engine_for("md", "epub").convert(
        markdown, epub, {"target_format": "epub", "source_format": "md"}
    )
    assert epub.exists()

    target = tmp_path / "book.mobi"
    CalibreEngine().convert(
        epub, target, {"target_format": "mobi", "source_format": "epub"}
    )
    assert target.exists() and target.stat().st_size > 0
