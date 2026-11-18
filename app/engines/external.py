"""Detection of optional external tools (Pandoc / LibreOffice / Calibre).

They are not used for conversions yet; the status is shown in the UI so users
know what will be enabled in a future release.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


class ExternalTool:
    def __init__(self, key: str, label_key: str, names: list[str], paths: list[str]) -> None:
        self.key = key
        self.label_key = label_key
        self._names = names
        self._paths = paths
        self._cached = False
        self._found: str | None = None

    def path(self) -> str | None:
        if self._cached:
            return self._found
        self._cached = True
        for name in self._names:
            found = shutil.which(name)
            if found:
                self._found = found
                return found
        for raw in self._paths:
            candidate = Path(os.path.expandvars(raw))
            if candidate.exists():
                self._found = str(candidate)
                return self._found
        self._found = None
        return None

    def available(self) -> bool:
        return self.path() is not None


EXTERNAL_TOOLS = [
    ExternalTool(
        "pandoc",
        "engine_pandoc",
        ["pandoc"],
        [
            r"%ProgramFiles%\Pandoc\pandoc.exe",
            r"%LOCALAPPDATA%\Pandoc\pandoc.exe",
            "/usr/local/bin/pandoc",
            "/opt/homebrew/bin/pandoc",
        ],
    ),
    ExternalTool(
        "libreoffice",
        "engine_libreoffice",
        ["soffice"],
        [
            r"%ProgramFiles%\LibreOffice\program\soffice.exe",
            r"%ProgramFiles(x86)%\LibreOffice\program\soffice.exe",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/usr/bin/soffice",
        ],
    ),
    ExternalTool(
        "calibre",
        "engine_calibre",
        ["ebook-convert"],
        [
            r"%ProgramFiles%\Calibre2\ebook-convert.exe",
            "/Applications/calibre.app/Contents/MacOS/ebook-convert",
            "/usr/bin/ebook-convert",
        ],
    ),
]
