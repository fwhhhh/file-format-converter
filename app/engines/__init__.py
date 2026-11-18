"""Conversion engine registry."""

from __future__ import annotations

from pathlib import Path

from ..core.formats import group_of
from .archive import ArchiveEngine
from .base import Engine, EngineError
from .external import EXTERNAL_TOOLS
from .image import ImageEngine
from .media import MediaEngine
from .table import TableEngine
from .text import TextEngine

_IMAGE_ENGINE = ImageEngine()
_MEDIA_ENGINE = MediaEngine()
_ENGINES: list[Engine] = [
    _IMAGE_ENGINE,
    _MEDIA_ENGINE,
    ArchiveEngine(),
    TextEngine(),
    TableEngine(),
]


def engines() -> list[Engine]:
    return list(_ENGINES)


def targets_for(src_ext: str) -> list[str]:
    result: list[str] = []
    for engine in _ENGINES:
        if not engine.available():
            continue
        for target in engine.targets(src_ext):
            if target not in result:
                result.append(target)
    return result


def engine_for(src_ext: str, target_ext: str) -> Engine | None:
    for engine in _ENGINES:
        if not engine.available():
            continue
        if target_ext in engine.targets(src_ext):
            return engine
    return None


def probe_metadata(ext: str, path: Path) -> dict:
    group = group_of(ext)
    try:
        if group == "image":
            return _IMAGE_ENGINE.probe(path)
        if group in ("video", "audio"):
            return _MEDIA_ENGINE.probe(path)
    except Exception:
        return {}
    return {}


def status_entries() -> list[tuple[str, str, bool]]:
    """Return (key, label_key, available) for built-in and optional engines."""
    result: list[tuple[str, str, bool]] = []
    for engine in _ENGINES:
        try:
            available = engine.available()
        except Exception:
            available = False
        result.append((engine.key, engine.label_key, available))
    for tool in EXTERNAL_TOOLS:
        result.append((tool.key, tool.label_key, tool.available()))
    return result


def ffmpeg_available() -> bool:
    return _MEDIA_ENGINE.available()


__all__ = [
    "Engine",
    "EngineError",
    "engine_for",
    "engines",
    "ffmpeg_available",
    "probe_metadata",
    "status_entries",
    "targets_for",
]
