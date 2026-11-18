"""Engine interface."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


class EngineError(Exception):
    """Raised when a conversion cannot be completed."""


Progress = Callable[[float], None]


class Engine:
    key = ""
    label_key = ""

    def available(self) -> bool:
        raise NotImplementedError

    def targets(self, src_ext: str) -> list[str]:
        return []

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        raise NotImplementedError

    def artifact_name(self, stem: str, target: str) -> str:
        """Return the output filename for a target format.

        Most engines produce ``<stem>.<target>``; engines that emit an archive
        of several files (PDF to page images) can override this.
        """
        return f"{stem}.{target}"

    def probe(self, path: Path) -> dict:
        return {}

    def can_read(self, ext: str) -> bool:
        return bool(self.targets(ext))
