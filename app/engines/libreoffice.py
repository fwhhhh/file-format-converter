"""LibreOffice fallback for document conversions."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..core.utils import project_root
from .base import Engine, EngineError, Progress

_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

WORD_SOURCES = {"docx", "doc", "odt", "rtf"}
EXCEL_SOURCES = {"xlsx", "xls"}
POWERPOINT_SOURCES = {"pptx", "ppt"}

_CACHE: dict[str, str | None] = {}


def find_soffice() -> str | None:
    if "soffice" in _CACHE:
        return _CACHE["soffice"]
    bundled = project_root() / "vendor" / "libreoffice" / "program" / "soffice.exe"
    found: str | None = str(bundled) if bundled.exists() else None
    if found is None:
        found = shutil.which("soffice")
    if found is None:
        candidates = [
            Path("C:/Program Files/LibreOffice/program/soffice.exe"),
            Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
            Path.home() / "AppData" / "Local" / "Programs" / "LibreOffice" / "program" / "soffice.exe",
            Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
            Path("/usr/bin/soffice"),
        ]
        for candidate in candidates:
            if candidate.exists():
                found = str(candidate)
                break
    _CACHE["soffice"] = found
    return found


class LibreOfficeEngine(Engine):
    key = "libreoffice"
    label_key = "engine_libreoffice"

    def available(self) -> bool:
        return find_soffice() is not None

    def targets(self, src_ext: str) -> list[str]:
        if not self.available():
            return []
        if src_ext in WORD_SOURCES or src_ext in POWERPOINT_SOURCES:
            return ["pdf"]
        if src_ext in EXCEL_SOURCES:
            result = ["pdf"]
            if src_ext == "xls":
                result.append("xlsx")
            return result
        return []

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        soffice = find_soffice()
        if soffice is None:
            raise EngineError("LibreOffice was not found")
        target = str(options.get("target_format") or dst.suffix.lower().lstrip("."))
        if target not in ("pdf", "xlsx"):
            raise EngineError(f"Unsupported LibreOffice target: {target}")

        temporary = Path(tempfile.mkdtemp(prefix="ffc_lo_"))
        outdir = temporary / "out"
        profile = temporary / "profile"
        outdir.mkdir()
        profile.mkdir()
        try:
            command = [
                soffice,
                "--headless",
                "--norestore",
                "--invisible",
                "--nodefault",
                "--nofirststartwizard",
                f"-env:UserInstallation={profile.as_uri()}",
                "--convert-to",
                target,
                "--outdir",
                str(outdir),
                str(src),
            ]
            if progress is not None:
                progress(0.1)
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
                creationflags=_CREATE_NO_WINDOW,
            )
            produced = sorted(outdir.glob(f"*.{target}"))
            if not produced:
                message = (completed.stderr or completed.stdout or "").strip()
                raise EngineError(
                    message[-1200:]
                    or f"LibreOffice exited with code {completed.returncode} without output"
                )
            shutil.move(str(produced[0]), str(dst))
            if progress is not None:
                progress(1.0)
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
