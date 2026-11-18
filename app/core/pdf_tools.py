"""PDF utilities used by the PDF toolbox."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from . import utils


def _open_reader(path: Path):
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Password protected PDF: {path.name}") from exc
    return reader


def page_count(path: Path) -> int:
    return len(_open_reader(path).pages)


def parse_page_ranges(spec: str, total: int) -> list[int]:
    """Parse ``1-3,5,8-10`` into 1-based page numbers."""
    text = spec.strip()
    if not text:
        return list(range(1, total + 1))
    for separator in ("，", "、", "；", ";"):
        text = text.replace(separator, ",")
    pages: list[int] = []
    for part in (piece.strip() for piece in text.split(",")):
        if not part:
            continue
        try:
            if "-" in part:
                start_text, end_text = part.split("-", 1)
                start = int(start_text)
                end = int(end_text)
                if start > end:
                    start, end = end, start
                if start < 1 or end > total:
                    raise ValueError
                numbers = range(start, end + 1)
            else:
                number = int(part)
                if number < 1 or number > total:
                    raise ValueError
                numbers = (number,)
        except ValueError as exc:
            raise ValueError(
                f"Invalid page range '{part}' (the PDF has {total} pages)"
            ) from exc
        for number in numbers:
            if number not in pages:
                pages.append(number)
    if not pages:
        raise ValueError("Empty page range")
    return pages


def merge_pdfs(sources: list[Path], output: Path) -> int:
    from pypdf import PdfWriter

    if len(sources) < 2:
        raise ValueError("Add at least two PDF files")
    writers = []
    writer = PdfWriter()
    try:
        for source in sources:
            reader = _open_reader(source)
            writers.append(reader)
            writer.append(reader)
        writer.write(str(output))
        return len(writer.pages)
    finally:
        writer.close()
        for reader in writers:
            try:
                reader.close()
            except Exception:
                pass


def extract_pages(source: Path, output: Path, page_spec: str) -> int:
    from pypdf import PdfWriter

    reader = _open_reader(source)
    writer = PdfWriter()
    try:
        total = len(reader.pages)
        pages = parse_page_ranges(page_spec, total)
        for number in pages:
            writer.add_page(reader.pages[number - 1])
        writer.write(str(output))
        return len(pages)
    finally:
        writer.close()
        try:
            reader.close()
        except Exception:
            pass


def split_pdf(
    source: Path,
    output_dir: Path,
    pages_per_file: int = 0,
    progress=None,
) -> list[Path]:
    from pypdf import PdfWriter

    reader = _open_reader(source)
    total = len(reader.pages)
    if total == 0:
        raise ValueError("The PDF has no pages")
    if pages_per_file <= 0:
        chunk_size = 1
    else:
        chunk_size = pages_per_file
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    try:
        chunk_index = 0
        for start in range(0, total, chunk_size):
            chunk_index += 1
            writer = PdfWriter()
            try:
                end = min(start + chunk_size, total)
                for index in range(start, end):
                    writer.add_page(reader.pages[index])
                if chunk_size == 1:
                    name = f"{source.stem}_page_{start + 1:03d}.pdf"
                else:
                    name = f"{source.stem}_part_{chunk_index:02d}.pdf"
                destination = utils.unique_path(output_dir, Path(name).stem, "pdf", set())
                writer.write(str(destination))
                written.append(destination)
            finally:
                writer.close()
            if progress is not None:
                progress((start + chunk_size) / total)
    finally:
        try:
            reader.close()
        except Exception:
            pass
    return written


def images_to_pdf(sources: list[Path], output: Path, dpi: int = 144) -> int:
    from PIL import Image, ImageOps

    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
    except Exception:
        pass
    if not sources:
        raise ValueError("Add at least one image")

    pages = []
    try:
        for source in sources:
            with Image.open(source) as image:
                image = ImageOps.exif_transpose(image)
                if image.mode in ("RGBA", "LA", "P"):
                    rgba = image.convert("RGBA")
                    background = Image.new("RGB", rgba.size, (255, 255, 255))
                    background.paste(rgba, mask=rgba.split()[-1])
                    page = background
                else:
                    page = image.convert("RGB")
                pages.append(page.copy())
        pages[0].save(
            str(output),
            format="PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=float(dpi),
        )
        return len(pages)
    finally:
        for page in pages:
            try:
                page.close()
            except Exception:
                pass


def pdf_to_images(
    source: Path,
    output_zip: Path,
    image_format: str = "png",
    dpi: int = 144,
    page_spec: str = "",
    quality: int = 85,
    progress=None,
) -> int:
    import pypdfium2 as pdfium

    target = image_format.lower()
    if target not in ("png", "jpg"):
        raise ValueError(f"Unsupported image format: {image_format}")
    temporary = Path(tempfile.mkdtemp(prefix="ffc_pdf_tool_"))
    document = None
    try:
        document = pdfium.PdfDocument(str(source))
        total = len(document)
        if total == 0:
            raise ValueError("The PDF has no pages")
        pages = parse_page_ranges(page_spec, total)
        images: list[Path] = []
        for index, number in enumerate(pages):
            page = document[number - 1]
            try:
                bitmap = page.render(scale=max(dpi, 36) / 72.0)
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
            path = temporary / f"{source.stem}_page_{number:03d}.{target}"
            if target == "jpg":
                image.convert("RGB").save(path, format="JPEG", quality=quality)
            else:
                image.save(path, format="PNG")
            images.append(path)
            if progress is not None:
                progress((index + 1) / len(pages))
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in images:
                archive.write(path, path.name)
        return len(images)
    finally:
        if document is not None:
            try:
                document.close()
            except Exception:
                pass
        shutil.rmtree(temporary, ignore_errors=True)
