"""Image conversions backed by Pillow (and pillow-heif for HEIC)."""

from __future__ import annotations

from pathlib import Path

from ..core.formats import IMAGE_EXTS
from .base import Engine, EngineError, Progress

_HEIF_REGISTERED = False

_FORMAT_BY_EXT = {
    "jpg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "bmp": "BMP",
    "gif": "GIF",
    "tiff": "TIFF",
    "ico": "ICO",
    "pdf": "PDF",
    "ppm": "PPM",
}


def _load_pil():
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    return Image


def _register_heif() -> None:
    global _HEIF_REGISTERED
    if _HEIF_REGISTERED:
        return
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
    except Exception:
        pass
    _HEIF_REGISTERED = True


class ImageEngine(Engine):
    key = "image"
    label_key = "engine_image"

    READABLE = set(IMAGE_EXTS)
    WRITABLE = ["png", "jpg", "webp", "bmp", "gif", "tiff", "ico", "pdf", "ppm"]

    def available(self) -> bool:
        try:
            import PIL  # noqa: F401
        except Exception:
            return False
        return True

    def targets(self, src_ext: str) -> list[str]:
        if src_ext not in self.READABLE:
            return []
        return [fmt for fmt in self.WRITABLE if fmt != src_ext]

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        Image = _load_pil()
        _register_heif()
        target = dst.suffix.lower().lstrip(".")
        fmt = _FORMAT_BY_EXT.get(target)
        if fmt is None:
            raise EngineError(f"Unsupported image target: {target}")
        quality = int(options.get("quality", 85))
        quality = max(1, min(100, quality))
        try:
            max_size = int(options.get("max_size", 0))
        except (TypeError, ValueError):
            max_size = 0
        max_size = max(0, max_size)
        try:
            with Image.open(src) as image:
                animated = bool(getattr(image, "is_animated", False))
                if fmt in ("GIF", "WEBP") and animated:
                    self._save_animation(Image, image, dst, fmt, quality, max_size)
                else:
                    self._save_still(Image, image, dst, fmt, quality, max_size)
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001 - surface Pillow errors to the UI
            raise EngineError(str(exc)) from exc
        if progress is not None:
            progress(1.0)

    def _save_still(
        self,
        Image,
        image,
        dst: Path,
        fmt: str,
        quality: int,
        max_size: int,
    ) -> None:
        frame = image
        if getattr(image, "is_animated", False):
            frame = image.copy()
        if max_size > 0:
            frame.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        if fmt in ("JPEG", "BMP", "PDF") and frame.mode in ("RGBA", "LA", "P"):
            rgba = frame.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            frame = background
        elif fmt in ("JPEG", "BMP", "PDF", "PPM"):
            frame = frame.convert("RGB")

        if fmt == "ICO":
            frame = frame.convert("RGBA")
            frame.thumbnail((256, 256))
            frame.save(dst, format="ICO", sizes=[frame.size])
            return
        if fmt == "PDF":
            frame.save(dst, format="PDF", resolution=96.0)
            return
        if fmt in ("JPEG", "WEBP"):
            frame.save(dst, format=fmt, quality=quality, optimize=True)
            return
        if fmt == "PPM":
            frame.convert("RGB").save(dst, format="PPM")
            return
        frame.save(dst, format=fmt)

    def _save_animation(
        self,
        Image,
        image,
        dst: Path,
        fmt: str,
        quality: int,
        max_size: int,
    ) -> None:
        from PIL import ImageSequence

        frames = []
        for frame in ImageSequence.Iterator(image):
            converted = frame.convert("RGBA")
            if max_size > 0:
                converted.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            frames.append(converted)
        if not frames:
            raise EngineError("No frames in image")
        duration = image.info.get("duration", 100)
        loop = image.info.get("loop", 0)
        save_kwargs = {
            "save_all": True,
            "append_images": frames[1:],
            "duration": duration,
            "loop": loop,
        }
        if fmt == "WEBP":
            save_kwargs["quality"] = quality
        frames[0].save(dst, format=fmt, **save_kwargs)

    def probe(self, path: Path) -> dict:
        try:
            Image = _load_pil()
            _register_heif()
            with Image.open(path) as image:
                return {
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                }
        except Exception:
            return {}
