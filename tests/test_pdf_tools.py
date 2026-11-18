from __future__ import annotations

import zipfile

import pytest

from app.core import pdf_tools


def _blank_pdf(path, pages: int) -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    try:
        for _ in range(pages):
            writer.add_blank_page(width=200, height=200)
        writer.write(str(path))
    finally:
        writer.close()


def test_parse_page_ranges():
    assert pdf_tools.parse_page_ranges("", 5) == [1, 2, 3, 4, 5]
    assert pdf_tools.parse_page_ranges("1-3,5", 5) == [1, 2, 3, 5]
    assert pdf_tools.parse_page_ranges("5, 1-2", 5) == [5, 1, 2]
    assert pdf_tools.parse_page_ranges("1，3", 5) == [1, 3]
    with pytest.raises(ValueError):
        pdf_tools.parse_page_ranges("0-2", 5)
    with pytest.raises(ValueError):
        pdf_tools.parse_page_ranges("4-8", 5)
    with pytest.raises(ValueError):
        pdf_tools.parse_page_ranges("abc", 5)


def test_merge_and_extract(tmp_path):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    _blank_pdf(first, 2)
    _blank_pdf(second, 3)

    merged = tmp_path / "merged.pdf"
    assert pdf_tools.merge_pdfs([first, second], merged) == 5
    assert pdf_tools.page_count(merged) == 5

    extracted = tmp_path / "extracted.pdf"
    assert pdf_tools.extract_pages(merged, extracted, "1,3,5") == 3
    assert pdf_tools.page_count(extracted) == 3


def test_split(tmp_path):
    source = tmp_path / "source.pdf"
    _blank_pdf(source, 5)

    per_page = tmp_path / "per_page"
    written = pdf_tools.split_pdf(source, per_page, 0)
    assert len(written) == 5
    assert all(path.exists() for path in written)

    chunks = tmp_path / "chunks"
    written = pdf_tools.split_pdf(source, chunks, 2)
    assert len(written) == 3
    assert pdf_tools.page_count(written[0]) == 2
    assert pdf_tools.page_count(written[-1]) == 1


def test_images_to_pdf_and_pdf_to_images(tmp_path):
    from PIL import Image

    images = []
    for index, color in enumerate(("red", "green", "blue")):
        path = tmp_path / f"image_{index}.png"
        Image.new("RGB", (120, 90), color).save(path)
        images.append(path)

    pdf = tmp_path / "album.pdf"
    assert pdf_tools.images_to_pdf(images, pdf, 96) == 3
    assert pdf_tools.page_count(pdf) == 3

    images_zip = tmp_path / "pages.zip"
    count = pdf_tools.pdf_to_images(
        pdf, images_zip, "png", 96, "2-3"
    )
    assert count == 2
    with zipfile.ZipFile(images_zip) as archive:
        names = archive.namelist()
    assert len(names) == 2
    assert any("page_002" in name for name in names)
    assert any("page_003" in name for name in names)
