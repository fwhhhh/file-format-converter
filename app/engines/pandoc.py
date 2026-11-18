"""Document conversions through Pandoc."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..core.utils import project_root
from .base import Engine, EngineError, Progress
from .external import EXTERNAL_TOOLS

_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

PANDOC_INPUT = {
    "md": "markdown",
    "html": "html",
    "txt": "markdown",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "epub": "epub",
}
PANDOC_OUTPUT = {
    "md": "gfm",
    "html": "html5",
    "txt": "plain",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "epub": "epub",
}
TEXT_SOURCES = {"md", "html", "txt"}

_CACHE: dict[str, str | None] = {}


def find_pandoc() -> str | None:
    if "pandoc" in _CACHE:
        return _CACHE["pandoc"]
    bundled = project_root() / "vendor" / "pandoc" / "pandoc.exe"
    found: str | None = str(bundled) if bundled.exists() else None
    if found is None:
        found = shutil.which("pandoc")
    if found is None:
        for tool in EXTERNAL_TOOLS:
            if tool.key == "pandoc":
                found = tool.path()
                break
    if found is None:
        candidates = [
            Path.home() / "AppData" / "Local" / "Pandoc" / "pandoc.exe",
            Path("C:/Program Files/Pandoc/pandoc.exe"),
            Path("/usr/local/bin/pandoc"),
            Path("/opt/homebrew/bin/pandoc"),
        ]
        for candidate in candidates:
            if candidate.exists():
                found = str(candidate)
                break
    _CACHE["pandoc"] = found
    return found


class PandocEngine(Engine):
    key = "pandoc"
    label_key = "engine_pandoc"

    def available(self) -> bool:
        return find_pandoc() is not None

    def targets(self, src_ext: str) -> list[str]:
        if src_ext not in PANDOC_INPUT:
            return []
        return [fmt for fmt in PANDOC_OUTPUT if fmt != src_ext]

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        pandoc = find_pandoc()
        if pandoc is None:
            raise EngineError("Pandoc was not found")
        source_ext = str(
            options.get("source_format") or src.suffix.lower().lstrip(".")
        )
        target = str(options.get("target_format") or dst.suffix.lower().lstrip("."))
        input_format = PANDOC_INPUT.get(source_ext)
        output_format = PANDOC_OUTPUT.get(target)
        if input_format is None or output_format is None:
            raise EngineError(f"Unsupported Pandoc conversion: {source_ext} -> {target}")

        temporary = None
        input_path = src
        if source_ext in TEXT_SOURCES:
            input_path, temporary = self._as_utf8(src, source_ext)
        try:
            command = [
                pandoc,
                "-f",
                input_format,
                "-t",
                output_format,
                "-o",
                str(dst),
            ]
            if target == "html":
                command.extend(["--standalone", "--embed-resources"])
            if target == "md":
                media_dir = dst.parent / f"{dst.stem}_media"
                command.append(f"--extract-media={media_dir}")
            command.append(f"--resource-path={src.parent}")
            command.append(str(input_path))
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
            if completed.returncode != 0:
                message = (completed.stderr or completed.stdout or "").strip()
                raise EngineError(message[-1200:] or f"Pandoc exited with {completed.returncode}")
            if not dst.exists():
                raise EngineError("Pandoc did not produce an output file")
            if progress is not None:
                progress(1.0)
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        finally:
            if temporary is not None:
                shutil.rmtree(temporary, ignore_errors=True)

    def _as_utf8(self, src: Path, ext: str) -> tuple[Path, Path | None]:
        data = src.read_bytes()
        try:
            data.decode("utf-8-sig")
            return src, None
        except UnicodeDecodeError:
            pass
        try:
            text = data.decode("gb18030")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        temporary = Path(tempfile.mkdtemp(prefix="ffc_pandoc_"))
        converted = temporary / f"input.{ext}"
        converted.write_text(text, encoding="utf-8")
        return converted, temporary
