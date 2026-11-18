"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Entry:
    entry_id: int
    path: Path
    ext: str
    size: int
    targets: list[str]
    meta: dict = field(default_factory=dict)


@dataclass
class OutputState:
    status: str = "waiting"  # waiting | running | done | failed
    path: Path | None = None
    error: str = ""
