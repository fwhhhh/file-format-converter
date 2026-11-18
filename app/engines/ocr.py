"""Small wrapper around the Tesseract OCR command line tool."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ..core.utils import project_root
from .base import EngineError

_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

_CACHE: dict[str, object] = {}


def find_tesseract() -> str | None:
    if "exe" in _CACHE:
        return _CACHE["exe"]  # type: ignore[return-value]
    exe_name = "tesseract.exe" if sys.platform == "win32" else "tesseract"
    found = shutil.which("tesseract")
    if found is None:
        roots = [
            os.environ.get("LOCALAPPDATA"),
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
        ]
        for root in roots:
            if not root:
                continue
            for sub in (Path(root) / "Tesseract-OCR", Path(root) / "Programs" / "Tesseract-OCR"):
                candidate = sub / exe_name
                if candidate.exists():
                    found = str(candidate)
                    break
            if found:
                break
    _CACHE["exe"] = found
    return found


def bundled_tessdata() -> Path | None:
    directory = project_root() / "vendor" / "tessdata"
    if directory.is_dir():
        return directory
    return None


def _system_languages(executable: str) -> set[str]:
    try:
        completed = subprocess.run(
            [executable, "--list-langs"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            creationflags=_CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    names: set[str] = set()
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("list of available"):
            continue
        names.add(line)
    return names


def languages() -> str:
    if "lang" in _CACHE:
        return _CACHE["lang"]  # type: ignore[return-value]
    executable = find_tesseract()
    if executable is None:
        _CACHE["lang"] = ""
        return ""
    directory = bundled_tessdata()
    names: set[str] = set()
    if directory is not None:
        names = {path.stem for path in directory.glob("*.traineddata")}
    if "chi_sim" not in names or "eng" not in names:
        names |= _system_languages(executable)
    selected = ""
    if "chi_sim" in names and "eng" in names:
        selected = "chi_sim+eng"
    elif "chi_sim" in names:
        selected = "chi_sim"
    elif "eng" in names:
        selected = "eng"
    _CACHE["lang"] = selected
    return selected


def available() -> bool:
    return bool(find_tesseract() and languages())


def ocr_image(image_path: Path) -> str:
    executable = find_tesseract()
    lang = languages()
    if executable is None or not lang:
        raise EngineError("Tesseract OCR is not installed")
    command = [executable, str(image_path), "stdout", "-l", lang, "--psm", "3"]
    directory = bundled_tessdata()
    if directory is not None:
        command.extend(["--tessdata-dir", str(directory)])
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            creationflags=_CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EngineError(str(exc)) from exc
    if completed.returncode != 0:
        message = (completed.stderr or "").strip()
        raise EngineError(message[-800:] or "Tesseract failed")
    return completed.stdout.strip()
