"""PDF source conversions: page images and text extraction."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from .base import CancelledError, Engine, EngineError, Progress


def _has_pdfium() -> bool:
    try:
        import pypdfium2  # noqa: F401
    except Exception:
        return False
    return True


def _has_pypdf() -> bool:
    try:
        import pypdf  # noqa: F401
    except Exception:
        return False
    return True


def _has_python_docx() -> bool:
    try:
        import docx  # noqa: F401
    except Exception:
        return False
    return True


class PdfEngine(Engine):
    key = "pdf"
    label_key = "engine_pdf"

    def available(self) -> bool:
        return _has_pdfium() or _has_pypdf()

    def targets(self, src_ext: str) -> list[str]:
        if src_ext != "pdf":
            return []
        result: list[str] = []
        if _has_pdfium():
            result.extend(["png", "jpg"])
        if _has_pypdf():
            result.append("txt")
        if _has_pdfium() and _has_python_docx():
            try:
                from .ocr import available as ocr_available

                if ocr_available():
                    result.append("docx_ocr")
            except Exception:
                pass
        return result

    def artifact_name(self, stem: str, target: str) -> str:
        if target in ("png", "jpg"):
            return f"{stem}_{target}.zip"
        if target == "docx_ocr":
            return f"{stem}_ocr.docx"
        return super().artifact_name(stem, target)

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        target = str(options.get("target_format") or dst.suffix.lower().lstrip("."))
        if self._cancel_requested(options):
            raise CancelledError()
        if target == "txt":
            self._extract_text(src, dst, options, progress)
            return
        if target in ("png", "jpg"):
            self._render_pages(src, dst, target, options, progress)
            return
        if target == "docx_ocr":
            self._ocr_to_docx(src, dst, options, progress)
            return
        raise EngineError(f"Unsupported PDF target: {target}")

    @staticmethod
    def _cancel_requested(options: dict) -> bool:
        event = options.get("cancel_event")
        return event is not None and event.is_set()

    # ------------------------------------------------------------- text

    def _extract_text(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None,
    ) -> None:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(src))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception as exc:  # noqa: BLE001
                    raise EngineError("This PDF is password protected") from exc
            pages = reader.pages
            total = len(pages)
            if total == 0:
                raise EngineError("This PDF has no pages")
            parts: list[str] = []
            for page in pages:
                if self._cancel_requested(options):
                    raise CancelledError()
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text.strip())
            result = "\n\n".join(parts).strip()
            if not result:
                from .ocr import available as ocr_available

                if ocr_available():
                    self._ocr_pages(src, dst, options, progress)
                    return
                raise EngineError(
                    "No text layer found in this PDF (scanned document). "
                    "Install Tesseract OCR to read scanned PDFs."
                )
            dst.write_text(result + "\n", encoding="utf-8")
        except EngineError:
            raise
        except CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        if progress is not None:
            progress(1.0)

    def _ocr_pages(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None,
    ) -> None:
        try:
            import pypdfium2 as pdfium

            from .ocr import ocr_image
        except Exception as exc:  # noqa: BLE001
            raise EngineError("PDF OCR requires pypdfium2 and Tesseract") from exc
        temporary = Path(tempfile.mkdtemp(prefix="ffc_ocr_"))
        document = None
        try:
            document = pdfium.PdfDocument(str(src))
            total = len(document)
            if total == 0:
                raise EngineError("This PDF has no pages")
            parts: list[str] = []
            for index in range(total):
                if self._cancel_requested(options):
                    raise CancelledError()
                page = document[index]
                try:
                    bitmap = page.render(scale=2.5)
                    try:
                        image = bitmap.to_pil()
                    finally:
                        try:
                            bitmap.close()
                        except Exception:
                            pass
                finally:
                    try:
                        page.close()
                    except Exception:
                        pass
                image_path = temporary / f"page_{index + 1:03d}.png"
                image.save(image_path, format="PNG")
                text = ocr_image(image_path)
                if text.strip():
                    parts.append(text.strip())
                if progress is not None:
                    progress(0.1 + 0.85 * (index + 1) / total)
            result = "\n\n".join(parts).strip()
            if not result:
                raise EngineError("OCR found no text in this PDF")
            dst.write_text(result + "\n", encoding="utf-8")
        except EngineError:
            raise
        except CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        finally:
            if document is not None:
                try:
                    document.close()
                except Exception:
                    pass
            shutil.rmtree(temporary, ignore_errors=True)
        if progress is not None:
            progress(1.0)

    # ------------------------------------------------------------- docx

    def _ocr_to_docx(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None,
    ) -> None:
        try:
            import pypdfium2 as pdfium
            from docx import Document
            from docx.enum.section import WD_SECTION
            from docx.oxml.ns import qn
            from docx.shared import Inches, Pt

            from .ocr import ocr_layout
        except Exception as exc:  # noqa: BLE001
            raise EngineError(
                "PDF OCR to Word requires pypdfium2, Tesseract and python-docx"
            ) from exc

        temporary = Path(tempfile.mkdtemp(prefix="ffc_ocr_docx_"))
        pdf_document = None
        try:
            pdf_document = pdfium.PdfDocument(str(src))
            total = len(pdf_document)
            if total == 0:
                raise EngineError("This PDF has no pages")
            pages: list[tuple[float, float, list[dict]]] = []
            for index in range(total):
                if self._cancel_requested(options):
                    raise CancelledError()
                page = pdf_document[index]
                try:
                    try:
                        width_points, height_points = page.get_size()
                    except Exception:
                        width_points, height_points = 595.0, 842.0
                    bitmap = page.render(scale=2.5)
                    try:
                        image = bitmap.to_pil()
                    finally:
                        try:
                            bitmap.close()
                        except Exception:
                            pass
                finally:
                    try:
                        page.close()
                    except Exception:
                        pass
                image_path = temporary / f"page_{index + 1:03d}.png"
                image.save(image_path, format="PNG")
                pages.append(
                    (
                        float(width_points),
                        float(height_points),
                        ocr_layout(image_path),
                    )
                )
                if progress is not None:
                    progress(0.1 + 0.85 * (index + 1) / total)
            if not any(lines for _width, _height, lines in pages):
                raise EngineError("OCR found no text in this PDF")

            word_document = Document()
            try:
                style = word_document.styles["Normal"]
                style.font.name = "Microsoft YaHei"
                style.font.size = Pt(10.5)
                try:
                    style.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
                except Exception:
                    pass
            except Exception:
                pass

            for page_index, (width_points, height_points, lines) in enumerate(pages):
                if page_index == 0:
                    section = word_document.sections[0]
                else:
                    section = word_document.add_section(WD_SECTION.NEW_PAGE)
                section.page_width = Inches(max(width_points, 72.0) / 72.0)
                section.page_height = Inches(max(height_points, 72.0) / 72.0)
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.5)
                section.right_margin = Inches(0.5)

                groups: dict[tuple[int, int], list[dict]] = {}
                order: list[tuple[int, int]] = []
                for line in lines:
                    key = (int(line["block"]), int(line["par"]))
                    if key not in groups:
                        groups[key] = []
                        order.append(key)
                    groups[key].append(line)
                for key in order:
                    paragraph_lines = groups[key]
                    paragraph = word_document.add_paragraph()
                    try:
                        paragraph.paragraph_format.space_after = Pt(4)
                        left_points = paragraph_lines[0]["left"] * 72.0 / 180.0
                        indent = max(0.0, min(144.0, left_points - 36.0))
                        paragraph.paragraph_format.left_indent = Pt(indent)
                    except Exception:
                        pass
                    for line_index, line in enumerate(paragraph_lines):
                        run = paragraph.add_run(line["text"])
                        try:
                            run.font.name = "Microsoft YaHei"
                            run.font.size = Pt(float(line["font_pt"]))
                            run._element.rPr.rFonts.set(
                                qn("w:eastAsia"), "Microsoft YaHei"
                            )
                        except Exception:
                            pass
                        if line_index != len(paragraph_lines) - 1:
                            run.add_break()
            word_document.save(str(dst))
        except EngineError:
            raise
        except CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        finally:
            if pdf_document is not None:
                try:
                    pdf_document.close()
                except Exception:
                    pass
            shutil.rmtree(temporary, ignore_errors=True)
        if progress is not None:
            progress(1.0)

    # ----------------------------------------------------------- images

    def _render_pages(
        self,
        src: Path,
        dst: Path,
        target: str,
        options: dict,
        progress: Progress | None,
    ) -> None:
        try:
            import pypdfium2 as pdfium
        except Exception as exc:  # noqa: BLE001
            raise EngineError("pypdfium2 is required for PDF page rendering") from exc

        quality = int(options.get("quality", 85))
        quality = max(1, min(100, quality))
        try:
            dpi = int(options.get("dpi", 144))
        except (TypeError, ValueError):
            dpi = 144
        scale = max(dpi, 36) / 72.0
        if self._cancel_requested(options):
            raise CancelledError()
        temporary = Path(tempfile.mkdtemp(prefix="ffc_pdf_"))
        document = None
        try:
            document = pdfium.PdfDocument(str(src))
            total = len(document)
            if total == 0:
                raise EngineError("This PDF has no pages")
            images: list[Path] = []
            for index in range(total):
                if self._cancel_requested(options):
                    raise CancelledError()
                page = document[index]
                try:
                    bitmap = page.render(scale=scale)
                    try:
                        image = bitmap.to_pil()
                    finally:
                        try:
                            bitmap.close()
                        except Exception:
                            pass
                finally:
                    try:
                        page.close()
                    except Exception:
                        pass
                image_path = temporary / f"{src.stem}_page_{index + 1:03d}.{target}"
                if target == "jpg":
                    image = image.convert("RGB")
                    image.save(image_path, format="JPEG", quality=quality)
                else:
                    image.save(image_path, format="PNG")
                images.append(image_path)
                if progress is not None:
                    progress(0.1 + 0.85 * (index + 1) / total)
            with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as archive:
                for image_path in images:
                    archive.write(image_path, image_path.name)
        except EngineError:
            raise
        except CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        finally:
            if document is not None:
                try:
                    document.close()
                except Exception:
                    pass
            shutil.rmtree(temporary, ignore_errors=True)
        if progress is not None:
            progress(1.0)

    def probe(self, path: Path) -> dict:
        try:
            from pypdf import PdfReader

            return {"pages": len(PdfReader(str(path)).pages)}
        except Exception:
            pass
        try:
            import pypdfium2 as pdfium

            document = pdfium.PdfDocument(str(path))
            try:
                return {"pages": len(document)}
            finally:
                document.close()
        except Exception:
            return {}
