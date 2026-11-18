from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.engines import engine_for, targets_for
from app.engines.office import find_office_exe
from app.engines.pdf import PdfEngine

WORD_MISSING = find_office_exe("word") is None
POWERPOINT_MISSING = find_office_exe("powerpoint") is None


def _write_minimal_docx(path: Path) -> None:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Hello PDF</w:t></w:r></w:p><w:sectPr/></w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)


@pytest.mark.skipif(WORD_MISSING, reason="Microsoft Word is not installed")
def test_office_targets():
    assert "pdf" in targets_for("docx")
    assert "pdf" in targets_for("doc")
    assert "docx" in targets_for("pdf")
    if find_office_exe("excel"):
        assert "pdf" in targets_for("xlsx")
    if find_office_exe("powerpoint"):
        assert "pdf" in targets_for("pptx")


@pytest.mark.skipif(WORD_MISSING, reason="Microsoft Word is not installed")
def test_docx_to_pdf_and_pdf_to_docx(tmp_path):
    docx = tmp_path / "sample.docx"
    _write_minimal_docx(docx)
    pdf = tmp_path / "sample.pdf"

    engine = engine_for("docx", "pdf")
    assert engine is not None
    engine.convert(docx, pdf, {"target_format": "pdf", "source_format": "docx"})
    assert pdf.read_bytes().startswith(b"%PDF")

    back = tmp_path / "sample_back.docx"
    engine = engine_for("pdf", "docx")
    assert engine is not None
    engine.convert(pdf, back, {"target_format": "docx", "source_format": "pdf"})
    with zipfile.ZipFile(back) as archive:
        assert "word/document.xml" in archive.namelist()


@pytest.mark.skipif(WORD_MISSING, reason="Microsoft Word is not installed")
def test_pdf_to_png_zip_and_text(tmp_path):
    docx = tmp_path / "sample.docx"
    _write_minimal_docx(docx)
    pdf = tmp_path / "sample.pdf"
    engine_for("docx", "pdf").convert(
        docx, pdf, {"target_format": "pdf", "source_format": "docx"}
    )

    pdf_engine = PdfEngine()
    assert pdf_engine.available()

    pages = tmp_path / "sample_png.zip"
    pdf_engine.convert(pdf, pages, {"target_format": "png", "quality": 85})
    with zipfile.ZipFile(pages) as archive:
        names = archive.namelist()
    assert names and all(name.endswith(".png") for name in names)

    text_path = tmp_path / "sample.txt"
    pdf_engine.convert(pdf, text_path, {"target_format": "txt"})
    assert "Hello" in text_path.read_text(encoding="utf-8")


@pytest.mark.skipif(find_office_exe("excel") is None, reason="Excel not installed")
def test_xlsx_to_pdf(tmp_path):
    from openpyxl import Workbook

    source = tmp_path / "sample.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["name", "value"])
    sheet.append(["hello", 1])
    workbook.save(source)

    target = tmp_path / "sample.pdf"
    engine = engine_for("xlsx", "pdf")
    assert engine is not None
    engine.convert(source, target, {"target_format": "pdf", "source_format": "xlsx"})
    assert target.read_bytes().startswith(b"%PDF")


@pytest.mark.skipif(POWERPOINT_MISSING, reason="PowerPoint not installed")
def test_pptx_to_pdf(tmp_path):
    import pythoncom
    import win32com.client

    source = tmp_path / "sample.pptx"
    pythoncom.CoInitialize()
    powerpoint = None
    try:
        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        presentation = powerpoint.Presentations.Add()
        slide = presentation.Slides.Add(1, 1)
        slide.Shapes.Title.TextFrame.TextRange.Text = "Hello PPT"
        presentation.SaveAs(str(source), 24)
        presentation.Close()
    finally:
        if powerpoint is not None:
            powerpoint.Quit()
        pythoncom.CoUninitialize()

    target = tmp_path / "sample.pdf"
    engine = engine_for("pptx", "pdf")
    assert engine is not None
    engine.convert(source, target, {"target_format": "pdf", "source_format": "pptx"})
    assert target.read_bytes().startswith(b"%PDF")
