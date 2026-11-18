"""E-book conversions through Calibre's ``ebook-convert``."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..core.utils import project_root
from .base import Engine, EngineError, Progress

_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

EBOOK_SOURCES = {"epub", "mobi", "azw3"}
EBOOK_TARGETS = ["epub", "mobi", "azw3", "pdf", "txt"]

_CACHE: dict[str, str | None] = {}


def find_ebook_convert() -> str | None:
    if "ebook-convert" in _CACHE:
        return _CACHE["ebook-convert"]
    bundled = project_root() / "vendor" / "calibre" / "ebook-convert.exe"
    found: str | None = str(bundled) if bundled.exists() else None
    if found is None:
        found = shutil.which("ebook-convert")
    if found is None:
        candidates = [
            Path("C:/Program Files/Calibre2/ebook-convert.exe"),
            Path("C:/Program Files (x86)/Calibre2/ebook-convert.exe"),
            Path.home() / "AppData" / "Local" / "Programs" / "Calibre2" / "ebook-convert.exe",
            Path("/Applications/calibre.app/Contents/MacOS/ebook-convert"),
            Path("/usr/bin/ebook-convert"),
        ]
        for candidate in candidates:
            if candidate.exists():
                found = str(candidate)
                break
    _CACHE["ebook-convert"] = found
    return found


class CalibreEngine(Engine):
    key = "calibre"
    label_key = "engine_calibre"

    def available(self) -> bool:
        return find_ebook_convert() is not None

    def targets(self, src_ext: str) -> list[str]:
        if src_ext not in EBOOK_SOURCES:
            return []
        return [fmt for fmt in EBOOK_TARGETS if fmt != src_ext]

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        executable = find_ebook_convert()
        if executable is None:
            raise EngineError("Calibre ebook-convert was not found")
        temporary = Path(tempfile.mkdtemp(prefix="ffc_calibre_"))
        environment = dict(os.environ)
        environment["CALIBRE_CONFIG_DIRECTORY"] = str(temporary / "config")
        environment["CALIBRE_TEMP_DIR"] = str(temporary / "tmp")
        Path(environment["CALIBRE_CONFIG_DIRECTORY"]).mkdir(parents=True, exist_ok=True)
        Path(environment["CALIBRE_TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
        try:
            if progress is not None:
                progress(0.1)
            completed = subprocess.run(
                [executable, str(src), str(dst)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
                env=environment,
                creationflags=_CREATE_NO_WINDOW,
            )
            if completed.returncode != 0 or not dst.exists():
                message = (completed.stderr or completed.stdout or "").strip()
                raise EngineError(
                    message[-1200:]
                    or f"Calibre exited with code {completed.returncode}"
                )
            if progress is not None:
                progress(1.0)
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
