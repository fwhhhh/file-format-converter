"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from . import __version__, i18n
from .core.utils import resource_path


def _write_minimal_docx(path: Path) -> None:
    """Create a tiny but valid .docx used by the self-test."""
    import zipfile

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


def run_selftest() -> int:
    """Hidden ``--selftest`` mode used to verify a packaged build."""
    import csv
    import struct
    import tempfile
    import wave
    import zipfile

    temp_root = Path(tempfile.mkdtemp(prefix="ffc_selftest_"))
    lines: list[str] = []
    cases: list[tuple[Path, str]] = []
    try:
        from PIL import Image, features

        image_path = temp_root / "image.png"
        Image.new("RGB", (64, 48), "red").save(image_path)
        cases.extend([(image_path, "jpg"), (image_path, "webp"), (image_path, "pdf")])
        if features.check("avif"):
            cases.append((image_path, "avif"))

        md_path = temp_root / "note.md"
        md_path.write_text("# Title\n\nHello **world**\n", encoding="utf-8")
        cases.append((md_path, "html"))

        csv_path = temp_root / "data.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows([["a", "b"], [1, 2]])
        cases.append((csv_path, "xlsx"))

        zip_path = temp_root / "data.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("a.txt", "hello")
        cases.append((zip_path, "7z"))

        wav_path = temp_root / "tone.wav"
        with wave.open(str(wav_path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(22050)
            handle.writeframes(b"".join(struct.pack("<h", 2000) for _ in range(4410)))
        cases.append((wav_path, "mp3"))

        try:
            import pillow_heif

            pillow_heif.register_heif_opener()
            heic_path = temp_root / "photo.heic"
            Image.new("RGB", (32, 24), "orange").save(heic_path, format="HEIF")
            cases.append((heic_path, "png"))
        except Exception:
            lines.append("SKIP HEIC support")

        from .core import detect
        from .engines import engine_for
        from .engines.ocr import available as ocr_available
        from .engines.office import find_office_exe
        from .engines.pandoc import find_pandoc
        from .engines.pdf import PdfEngine

        for source, target in cases:
            source_ext = detect.sniff_ext(source)
            engine = engine_for(source_ext, target)
            try:
                if engine is None:
                    raise RuntimeError(f"no engine for {source_ext} -> {target}")
                destination = temp_root / engine.artifact_name(source.stem, target)
                engine.convert(
                    source,
                    destination,
                    {
                        "quality": 85,
                        "preset": "balanced",
                        "target_format": target,
                        "source_format": source_ext,
                    },
                )
                lines.append(f"OK   {source.name} -> {target} ({destination.stat().st_size} bytes)")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL {source.name} -> {target}: {exc}")

        word_ready = find_office_exe("word") is not None
        if word_ready:
            try:
                docx_path = temp_root / "sample.docx"
                _write_minimal_docx(docx_path)
                pdf_path = temp_root / "sample.pdf"
                engine = engine_for("docx", "pdf")
                if engine is None:
                    raise RuntimeError("no Office engine")
                engine.convert(
                    docx_path,
                    pdf_path,
                    {"target_format": "pdf", "source_format": "docx"},
                )
                lines.append(f"OK   sample.docx -> pdf ({pdf_path.stat().st_size} bytes)")

                back_path = temp_root / "sample_back.docx"
                engine_for("pdf", "docx").convert(
                    pdf_path,
                    back_path,
                    {"target_format": "docx", "source_format": "pdf"},
                )
                with zipfile.ZipFile(back_path) as archive:
                    has_document = "word/document.xml" in archive.namelist()
                if not has_document:
                    raise RuntimeError("converted docx is missing word/document.xml")
                lines.append(f"OK   sample.pdf -> docx ({back_path.stat().st_size} bytes)")

                pdf_engine = PdfEngine()
                if pdf_engine.available():
                    png_path = temp_root / "sample_png.zip"
                    pdf_engine.convert(
                        pdf_path,
                        png_path,
                        {"target_format": "png", "quality": 85},
                    )
                    with zipfile.ZipFile(png_path) as archive:
                        page_names = [name for name in archive.namelist() if name.endswith(".png")]
                    if not page_names:
                        raise RuntimeError("PDF page rendering produced no images")
                    lines.append(f"OK   sample.pdf -> png zip ({len(page_names)} pages)")

                    txt_path = temp_root / "sample.txt"
                    pdf_engine.convert(pdf_path, txt_path, {"target_format": "txt"})
                    text = txt_path.read_text(encoding="utf-8")
                    if "Hello" not in text:
                        raise RuntimeError("PDF text extraction returned no text")
                    lines.append(f"OK   sample.pdf -> txt ({len(text)} chars)")
                else:
                    lines.append("SKIP PDF engine")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL Office/PDF pipeline: {exc}")
        else:
            lines.append("SKIP Microsoft Word not installed")

        if find_office_exe("excel") is not None:
            try:
                from openpyxl import Workbook

                xlsx_path = temp_root / "sample.xlsx"
                workbook = Workbook()
                sheet = workbook.active
                sheet.append(["name", "value"])
                sheet.append(["hello", 1])
                workbook.save(xlsx_path)
                xlsx_pdf = temp_root / "sample_xlsx.pdf"
                engine_for("xlsx", "pdf").convert(
                    xlsx_path,
                    xlsx_pdf,
                    {"target_format": "pdf", "source_format": "xlsx"},
                )
                lines.append(f"OK   sample.xlsx -> pdf ({xlsx_pdf.stat().st_size} bytes)")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL xlsx -> pdf: {exc}")
        else:
            lines.append("SKIP Microsoft Excel not installed")

        if find_pandoc() is not None:
            try:
                md_path = temp_root / "sample_pandoc.md"
                md_path.write_text("# 标题\n\nHello **world**\n", encoding="utf-8")
                docx_path = temp_root / "sample_pandoc.docx"
                engine_for("md", "docx").convert(
                    md_path,
                    docx_path,
                    {"target_format": "docx", "source_format": "md"},
                )
                back_md = temp_root / "sample_pandoc_back.md"
                engine_for("docx", "md").convert(
                    docx_path,
                    back_md,
                    {"target_format": "md", "source_format": "docx"},
                )
                text = back_md.read_text(encoding="utf-8")
                if "标题" not in text:
                    raise RuntimeError("Pandoc lost the Chinese text")
                lines.append(f"OK   sample_pandoc.md -> docx -> md ({len(text)} chars)")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL Pandoc pipeline: {exc}")
        else:
            lines.append("SKIP Pandoc not installed")

        if ocr_available():
            try:
                from PIL import Image, ImageDraw, ImageFont

                scan = Image.new("RGB", (900, 260), "white")
                draw = ImageDraw.Draw(scan)
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 84)
                except OSError:
                    font = ImageFont.load_default()
                draw.text((40, 70), "SCAN TEST 123", fill="black", font=font)
                scan_png = temp_root / "scan.png"
                scan.save(scan_png)
                scan_pdf = temp_root / "scan.pdf"
                engine_for("png", "pdf").convert(scan_png, scan_pdf, {})
                scan_txt = temp_root / "scan.txt"
                PdfEngine().convert(scan_pdf, scan_txt, {"target_format": "txt"})
                text = scan_txt.read_text(encoding="utf-8")
                if "SCAN" not in text and "123" not in text:
                    raise RuntimeError("OCR did not recognize the sample text")
                lines.append(f"OK   scanned pdf -> ocr txt ({len(text)} chars)")

                scan_docx = temp_root / "scan_ocr.docx"
                engine = engine_for("pdf", "docx_ocr")
                if engine is None:
                    raise RuntimeError("OCR to Word engine is unavailable")
                engine.convert(
                    scan_pdf,
                    scan_docx,
                    {"target_format": "docx_ocr", "source_format": "pdf"},
                )
                with zipfile.ZipFile(scan_docx) as archive:
                    document_xml = archive.read("word/document.xml").decode("utf-8")
                if "SCAN" not in document_xml and "123" not in document_xml:
                    raise RuntimeError("OCR to Word document has no recognized text")
                lines.append(f"OK   scanned pdf -> ocr docx ({scan_docx.stat().st_size} bytes)")

                layout_docx = temp_root / "sample_layout.docx"
                layout_engine = engine_for("pdf", "docx_layout")
                if layout_engine is None:
                    lines.append("SKIP PDF layout to Word")
                else:
                    layout_engine.convert(
                        pdf_path,
                        layout_docx,
                        {"target_format": "docx_layout", "source_format": "pdf"},
                    )
                    with zipfile.ZipFile(layout_docx) as archive:
                        layout_xml = archive.read("word/document.xml").decode("utf-8")
                    if "Hello" not in layout_xml:
                        raise RuntimeError("PDF layout to Word lost the text")
                    lines.append(
                        f"OK   sample.pdf -> layout docx ({layout_docx.stat().st_size} bytes)"
                    )
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL OCR pipeline: {exc}")
        else:
            lines.append("SKIP Tesseract OCR not available")

        from .engines.calibre import CalibreEngine, find_ebook_convert
        from .engines.libreoffice import LibreOfficeEngine, find_soffice

        if find_soffice() is not None:
            try:
                lo_docx = temp_root / "lo_sample.docx"
                _write_minimal_docx(lo_docx)
                lo_pdf = temp_root / "lo_sample.pdf"
                LibreOfficeEngine().convert(
                    lo_docx,
                    lo_pdf,
                    {"target_format": "pdf", "source_format": "docx"},
                )
                lines.append(f"OK   LibreOffice docx -> pdf ({lo_pdf.stat().st_size} bytes)")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL LibreOffice pipeline: {exc}")
        else:
            lines.append("SKIP LibreOffice not installed")

        if find_ebook_convert() is not None and find_pandoc() is not None:
            try:
                book_md = temp_root / "book.md"
                book_md.write_text("# Chapter\n\nHello e-book.\n", encoding="utf-8")
                book_epub = temp_root / "book.epub"
                engine_for("md", "epub").convert(
                    book_md,
                    book_epub,
                    {"target_format": "epub", "source_format": "md"},
                )
                book_mobi = temp_root / "book.mobi"
                CalibreEngine().convert(
                    book_epub,
                    book_mobi,
                    {"target_format": "mobi", "source_format": "epub"},
                )
                lines.append(f"OK   Calibre epub -> mobi ({book_mobi.stat().st_size} bytes)")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL Calibre pipeline: {exc}")
        else:
            lines.append("SKIP Calibre not installed")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"FAIL setup: {exc}")
    finally:
        import shutil

        shutil.rmtree(temp_root, ignore_errors=True)

    if getattr(sys, "frozen", False):
        output = Path(sys.executable).parent / "selftest.txt"
    else:
        output = Path.cwd() / "selftest.txt"
    try:
        output.write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        output = Path(tempfile.gettempdir()) / "ffc_selftest.txt"
        output.write_text("\n".join(lines), encoding="utf-8")
    return 0 if lines and all(line.startswith(("OK", "SKIP")) for line in lines) else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from .settings import Settings
    from .ui.main_window import MainWindow
    from .ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("FileFormatConverter")
    app.setOrganizationName("FileFormatConverter")
    app.setApplicationVersion(__version__)

    startup_paths = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    from .single_instance import SingleInstance

    guard = SingleInstance()
    if guard.acquire():
        # Listen before building the window so processes started by a
        # multi-file context-menu selection can connect right away.
        guard.listen()
    elif guard.notify_running(startup_paths, wait=3.0):
        return 0
    else:
        guard.listen(takeover=False)

    icon_path = resource_path("assets/app.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    settings = Settings()
    i18n.set_language(settings.language)
    apply_theme(app, settings.theme)

    def on_system_theme_changed(*_args: object) -> None:
        if settings.theme == "system":
            apply_theme(app, "system")

    try:
        app.styleHints().colorSchemeChanged.connect(on_system_theme_changed)
    except (AttributeError, TypeError):
        pass

    window = MainWindow(settings)
    guard.paths_received.connect(window.receive_paths)
    app.aboutToQuit.connect(guard.close)
    window.show()
    if startup_paths:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, lambda: window.add_paths(startup_paths))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
