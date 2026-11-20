"""Check GitHub Releases for a newer version."""

from __future__ import annotations

import json
import re
import urllib.request

from PySide6.QtCore import QObject, QRunnable, Signal

from .. import GITHUB_URL, __version__


def _repo_path() -> str:
    marker = "github.com/"
    if marker in GITHUB_URL:
        return GITHUB_URL.split(marker, 1)[1].strip("/")
    return "fwhhhh/file-format-converter"


def _version_tuple(text: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", text)
    if not numbers:
        return (0,)
    return tuple(int(number) for number in numbers[:3])


def fetch_latest() -> tuple[str, str] | None:
    repo = _repo_path()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/latest",
        headers={
            "User-Agent": "FileFormatConverter",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=6) as response:
        data = json.load(response)
    tag = str(data.get("tag_name") or "").strip()
    page = str(data.get("html_url") or "").strip()
    if not page:
        page = f"https://github.com/{repo}/releases/latest"
    if tag and _version_tuple(tag) > _version_tuple(__version__):
        return tag, page
    return None


class UpdateSignals(QObject):
    found = Signal(str, str)


class UpdateJob(QRunnable):
    def __init__(self, signals: UpdateSignals) -> None:
        super().__init__()
        self.signals = signals

    def run(self) -> None:
        try:
            result = fetch_latest()
        except Exception:
            return
        if result is not None:
            tag, page = result
            self.signals.found.emit(tag, page)
