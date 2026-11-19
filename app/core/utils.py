"""Small helpers shared across the application."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def human_size(size: int) -> str:
    if size < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            if value >= 100:
                return f"{value:.0f} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def format_duration(seconds: float | None) -> str:
    if seconds is None or seconds <= 0:
        return ""
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def stem_for(path: Path, ext: str) -> str:
    """Return the file name without its (possibly compound) extension."""
    suffix = "." + ext
    if path.name.lower().endswith(suffix):
        return path.name[: -len(suffix)]
    return path.stem


def sanitize_filename_part(text: str, limit: int = 120) -> str:
    """Strip characters that are not valid in a Windows file name."""
    if not text:
        return ""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", text)
    return cleaned.strip().rstrip(".")[:limit]


def sanitize_filename_suffix(text: str) -> str:
    return sanitize_filename_part(text, 32)


def expand_filename_template(
    template: str,
    stem: str,
    target: str,
    now: datetime | None = None,
) -> str:
    """Expand {name}, {target}, {date}, {time} in the output name template."""
    if not template or not template.strip():
        return stem
    moment = now or datetime.now()
    values = {
        "name": stem,
        "target": target,
        "ext": target,
        "date": moment.strftime("%Y%m%d"),
        "time": moment.strftime("%H%M%S"),
    }
    try:
        result = template.format(**values)
    except (KeyError, IndexError, ValueError):
        return stem
    cleaned = sanitize_filename_part(result, 120)
    return cleaned or stem


def unique_path(folder: Path, stem: str, ext: str, reserved: set[str]) -> Path:
    """Return a path that neither exists nor is already planned."""
    candidate = folder / f"{stem}.{ext}"
    index = 1
    while candidate.exists() or str(candidate).lower() in reserved:
        candidate = folder / f"{stem} ({index}).{ext}"
        index += 1
    reserved.add(str(candidate).lower())
    return candidate


def open_path(path: Path) -> None:
    """Open a file or folder with the system default handler."""
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return
    subprocess.Popen(["xdg-open", str(path)])


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


def resource_path(relative: str) -> Path:
    return project_root() / relative
