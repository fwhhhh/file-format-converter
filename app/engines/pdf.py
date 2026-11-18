"""PDF source conversions: page images and text extraction."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from .base import Engine, EngineError, Progress


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
        return result

    def artifact_name(self, stem: str, target: str) -> str:
        if target in ("png", "jpg"):
            return f"{stem}_{target}.zip"
        return super().artifact_name(stem, target)

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        target = str(options.get("target_format") or dst.suffix.lower().lstrip("."))
        if target == "txt":
            self._extract_text(src, dst, progress)
            return
        if target in ("png", "jpg"):
            self._render_pages(src, dst, target, options, progress)
            return
        raise EngineError(f"Unsupported PDF target: {target}")

    # ------------------------------------------------------------- text

    def _extract_text(self, src: Path, dst: Path, progress: Progress | None) -> None:
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
            for index, page in enumerate(pages):
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text.strip())
                if progress is not None:
                    progress(0.1 + 0.85 * (index + 1) / total)
            result = "\n\n".join(parts).strip()
            if not result:
                raise EngineError(
                    "No text layer found in this PDF (it may be a scanned document)"
                )
            dst.write_text(result + "\n", encoding="utf-8")
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
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
        temporary = Path(tempfile.mkdtemp(prefix="ffc_pdf_"))
        document = None
        try:
            document = pdfium.PdfDocument(str(src))
            total = len(document)
            if total == 0:
                raise EngineError("This PDF has no pages")
            images: list[Path] = []
            for index in range(total):
                page = document[index]
                try:
                    bitmap = page.render(scale=2.0)
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
