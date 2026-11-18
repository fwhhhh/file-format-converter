"""Format metadata shared by the detectors, engines and UI."""

from __future__ import annotations

from pathlib import Path

IMAGE_EXTS = ["jpg", "png", "webp", "bmp", "gif", "tiff", "ico", "heic", "ppm"]
VIDEO_EXTS = ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "ts", "mpg", "mpeg"]
AUDIO_EXTS = ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma"]
ARCHIVE_EXTS = ["zip", "7z", "tar", "tar.gz", "tar.bz2", "tar.xz", "gz", "bz2", "xz"]
TEXT_EXTS = ["txt", "md", "html"]
TABLE_EXTS = ["csv", "xlsx"]
DOCUMENT_EXTS = ["docx", "doc", "odt", "rtf", "pptx", "ppt", "xls", "pdf"]
EBOOK_EXTS = ["epub", "mobi", "azw3"]

ALL_EXTS = (
    IMAGE_EXTS
    + VIDEO_EXTS
    + AUDIO_EXTS
    + ARCHIVE_EXTS
    + TEXT_EXTS
    + TABLE_EXTS
    + DOCUMENT_EXTS
    + EBOOK_EXTS
)

_COMPOUND_SUFFIXES = ("tar.gz", "tar.bz2", "tar.xz")

_ALIASES = {
    "jpeg": "jpg",
    "jpe": "jpg",
    "jfif": "jpg",
    "tif": "tiff",
    "htm": "html",
    "markdown": "md",
    "tgz": "tar.gz",
    "tbz2": "tar.bz2",
    "tbz": "tar.bz2",
    "txz": "tar.xz",
    "mpeg": "mpg",
    "m4v": "m4v",
    "y4m": "y4m",
}

_EXT_SET = set(ALL_EXTS)


def normalize_ext(ext: str) -> str:
    ext = ext.lower().strip()
    if ext.startswith("."):
        ext = ext[1:]
    return _ALIASES.get(ext, ext)


def ext_of_path(path: Path) -> str:
    name = path.name.lower()
    for compound in _COMPOUND_SUFFIXES:
        if name.endswith("." + compound):
            return compound
    suffix = path.suffix
    if not suffix:
        return ""
    return normalize_ext(suffix)


def display(ext: str) -> str:
    return ext.upper()


def is_supported_ext(ext: str) -> bool:
    return ext in _EXT_SET


def group_of(ext: str) -> str:
    ext = normalize_ext(ext)
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in ARCHIVE_EXTS:
        return "archive"
    if ext in TEXT_EXTS:
        return "text"
    if ext in TABLE_EXTS:
        return "table"
    if ext in DOCUMENT_EXTS:
        return "document"
    if ext in EBOOK_EXTS:
        return "ebook"
    return "unknown"


def default_target(ext: str, targets: list[str]) -> str:
    """Pick a sensible default target format for automatic pre-selection."""
    if not targets:
        return ""
    group = group_of(ext)
    if group == "image" and ext == "gif" and "webp" in targets:
        return "webp"
    if group == "document":
        for candidate in ("pdf", "docx", "txt", "png", "jpg", "xlsx"):
            if candidate in targets:
                return candidate
        return targets[0]
    if group == "table":
        for candidate in ("pdf", "xlsx", "csv"):
            if candidate in targets:
                return candidate
        return targets[0]
    if group == "ebook":
        if ext == "epub":
            preference = ["pdf", "mobi", "azw3", "docx", "html", "md", "txt"]
        else:
            preference = ["epub", "pdf", "docx", "html", "md", "txt"]
        for candidate in preference:
            if candidate in targets:
                return candidate
        return targets[0]
    preference = {
        "image": ["png", "jpg", "webp"],
        "video": ["mp4", "mkv", "webm"],
        "audio": ["mp3", "m4a", "wav"],
        "archive": ["zip", "7z", "tar.gz"],
        "text": ["html", "md", "txt"],
        "table": ["xlsx", "csv"],
    }
    for candidate in preference.get(group, []):
        if candidate in targets:
            return candidate
    return targets[0]
