"""Detect the real format of a file by inspecting its leading bytes."""

from __future__ import annotations

from pathlib import Path

from .formats import AUDIO_EXTS, VIDEO_EXTS, ext_of_path

_ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1"}
_M4A_BRANDS = {b"m4a ", b"m4b ", b"m4p ", b"f4a "}
_AVIF_BRANDS = {b"avif", b"avis"}


def _read_head(path: Path, size: int = 4096) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read(size)
    except OSError:
        return b""


def sniff_ext(path: Path) -> str | None:
    """Return the normalized extension based on content, falling back to name."""
    head = _read_head(path)
    ext = ext_of_path(path)

    if not head:
        return ext if ext else None

    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head[:2] == b"BM":
        return "bmp"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    if head[:4] == b"\x00\x00\x01\x00":
        return "ico"
    if head[:4] == b"RIFF":
        kind = head[8:12]
        if kind == b"WEBP":
            return "webp"
        if kind == b"WAVE":
            return "wav"
        if kind == b"AVI ":
            return "avi"

    if head[:4] == b"ftyp":
        brand = head[8:12].lower()
        if brand in _AVIF_BRANDS:
            return "avif"
        if brand in _HEIF_BRANDS:
            return "heic"
        if brand in _M4A_BRANDS:
            return "m4a"
        if brand == b"qt  ":
            return "mov"
        if ext in ("mp4", "m4v", "mov", "m4a"):
            return ext
        return "mp4"

    if head.startswith(b"\x1a\x45\xdf\xa3"):
        if b"webm" in head[:64]:
            return "webm"
        return "mkv"

    if head[:2] in (b"\xff\xf1", b"\xff\xf9") or (len(head) > 2 and head[0] == 0xFF and (head[1] & 0xF6) == 0xF0):
        if ext == "aac":
            return "aac"
        return "aac"
    if head[:4] == b"fLaC":
        return "flac"
    if head[:4] == b"OggS":
        if ext == "opus":
            return "opus"
        return "ogg"
    if head.startswith(b"ID3") or (len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return "mp3"
    if head[:4] == b"\x30\x26\xb2\x75":
        if ext in ("wma", "wmv"):
            return ext
        return "wmv"
    if head[:3] == b"FLV":
        return "flv"

    if head.startswith(_ZIP_MAGIC):
        if ext in ("docx", "xlsx", "pptx", "epub", "odt"):
            return ext
        return "zip"
    if head.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "7z"
    if head.startswith(b"Rar!"):
        return "rar"
    if head[:2] == b"\x1f\x8b":
        if ext in ("tar.gz", "tgz"):
            return "tar.gz"
        return "gz"
    if head[:3] == b"BZh":
        if ext in ("tar.bz2", "tbz2", "tbz"):
            return "tar.bz2"
        return "bz2"
    if head[:6] == b"\xfd7zXZ\x00":
        if ext in ("tar.xz", "txz"):
            return "tar.xz"
        return "xz"
    if head[257:262] == b"ustar":
        return "tar"

    if head.startswith(_OLE_MAGIC):
        if ext in ("doc", "xls", "ppt", "wma", "wmv"):
            return ext
        return None
    if head.startswith(b"{\\rtf"):
        return "rtf"

    if head[:2] in (b"P6", b"P5", b"P3", b"P2") and len(head) > 2 and head[2] in b" \t\r\n":
        return "ppm"

    stripped = head.lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if stripped.startswith((b"<!doctype html", b"<html")):
        return "html"

    if ext:
        return ext
    return None


def is_supported(path: Path) -> bool:
    return sniff_ext(path) is not None
