"""Small wrapper around the Tesseract OCR command line tool."""

from __future__ import annotations

import os
import re
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
    bundled = project_root() / "vendor" / "tesseract" / exe_name
    found: str | None = str(bundled) if bundled.exists() else None
    if found is None:
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


_CJK_RE = re.compile(r"[㐀-鿿豈-﫿]")


def _is_cjk(character: str) -> bool:
    return bool(character and _CJK_RE.match(character))


def _join_tokens(tokens: list[str]) -> str:
    result = ""
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if not result:
            result = token
        elif _is_cjk(result[-1]) and _is_cjk(token[0]):
            result += token
        else:
            result += " " + token
    return result


def ocr_layout(image_path: Path) -> list[dict]:
    """Run Tesseract in TSV mode and return line boxes for layout rebuild.

    Each item contains block/paragraph/line identifiers, the recognized text,
    its bounding box in image pixels and an approximate font size in points
    (images are rendered at 180 DPI by the PDF engine).
    """
    executable = find_tesseract()
    lang = languages()
    if executable is None or not lang:
        raise EngineError("Tesseract OCR is not installed")
    command = [
        executable,
        str(image_path),
        "stdout",
        "-l",
        lang,
        "--psm",
        "3",
    ]
    directory = bundled_tessdata()
    if directory is not None:
        command.extend(["--tessdata-dir", str(directory)])
    command.append("tsv")
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

    groups: dict[tuple[int, int, int], dict] = {}
    order: list[tuple[int, int, int]] = []
    for row in completed.stdout.splitlines():
        columns = row.split("\t")
        if len(columns) < 12 or columns[0] == "level":
            continue
        if columns[0] != "5":
            continue
        text = columns[11].strip()
        if not text:
            continue
        try:
            block = int(columns[2])
            paragraph = int(columns[3])
            line = int(columns[4])
            left = int(columns[6])
            top = int(columns[7])
            width = int(columns[8])
            height = int(columns[9])
            confidence = float(columns[10])
        except ValueError:
            continue
        key = (block, paragraph, line)
        if key not in groups:
            groups[key] = {
                "block": block,
                "par": paragraph,
                "line": line,
                "tokens": [],
                "confidences": [],
                "left": left,
                "top": top,
                "right": left + width,
                "bottom": top + height,
                "heights": [],
            }
            order.append(key)
        group = groups[key]
        group["tokens"].append(text)
        if confidence >= 0:
            group["confidences"].append(confidence)
        group["left"] = min(group["left"], left)
        group["top"] = min(group["top"], top)
        group["right"] = max(group["right"], left + width)
        group["bottom"] = max(group["bottom"], top + height)
        if height > 0:
            group["heights"].append(height)

    lines: list[dict] = []
    for key in order:
        group = groups[key]
        text = _join_tokens(group["tokens"])
        if not text:
            continue
        heights = sorted(group["heights"])
        median_height = heights[len(heights) // 2] if heights else 0
        # Images rendered at scale 2.5 correspond to 180 DPI.
        font_points = median_height * 72.0 / 180.0
        font_points = max(7.0, min(40.0, font_points))
        confidences = group["confidences"]
        average_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )
        compact_text = text.replace(" ", "")
        has_cjk = any(_is_cjk(character) for character in compact_text)
        if (
            len(compact_text) <= 4
            and not has_cjk
            and average_confidence < 75.0
        ):
            # Drop tiny low-confidence Latin noise that Tesseract sometimes
            # invents above a title.
            continue
        lines.append(
            {
                "block": group["block"],
                "par": group["par"],
                "line": group["line"],
                "text": text,
                "left": group["left"],
                "top": group["top"],
                "width": group["right"] - group["left"],
                "height": group["bottom"] - group["top"],
                "font_pt": font_points,
                "confidence": average_confidence,
            }
        )
    return lines
