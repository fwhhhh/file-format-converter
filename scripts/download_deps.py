"""Download the FFmpeg LGPL shared build used for audio/video conversions.

Usage:
    python scripts/download_deps.py [--url URL]

Only the executables, DLLs and the license file are extracted into
``vendor/ffmpeg``.  The directory is ignored by git and included in release
packages by the build script.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-lgpl-shared.zip"
)

WANTED_SUFFIXES = (".exe", ".dll")
WANTED_LICENSES = {"LICENSE.txt", "LICENSE"}


def download(url: str, destination: Path) -> None:
    print(f"Downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        total = int(response.headers.get("Content-Length") or 0)
        with open(destination, "wb") as handle:
            copied = 0
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                handle.write(chunk)
                copied += len(chunk)
                if total:
                    percent = copied * 100 / total
                    print(f"\r  {copied / 1048576:6.1f} MiB / {total / 1048576:6.1f} MiB "
                          f"({percent:5.1f}%)", end="", flush=True)
    print()


def extract(archive_path: Path, root: Path) -> None:
    bin_dir = root / "vendor" / "ffmpeg" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            normalized = info.filename.replace("\\", "/")
            name = normalized.rsplit("/", 1)[-1]
            if not name or normalized.endswith("/"):
                continue
            if "/bin/" in normalized and name.lower().endswith(WANTED_SUFFIXES):
                target = bin_dir / name
                print(f"Extracting {name}")
                with archive.open(info) as source, open(target, "wb") as destination:
                    shutil.copyfileobj(source, destination)
            elif name in WANTED_LICENSES and normalized.count("/") == 1:
                target = root / "vendor" / "ffmpeg" / "FFMPEG_LICENSE.txt"
                print(f"Extracting {name}")
                with archive.open(info) as source, open(target, "wb") as destination:
                    shutil.copyfileobj(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download FFmpeg for Windows")
    parser.add_argument("--url", default=DEFAULT_URL, help="FFmpeg zip archive URL")
    parser.add_argument("--force", action="store_true", help="download even if present")
    args = parser.parse_args()

    if sys.platform != "win32":
        print("This script downloads a Windows build. Install ffmpeg with your "
              "package manager instead.")
        return 1

    root = Path(__file__).resolve().parents[1]
    target = root / "vendor" / "ffmpeg" / "bin" / "ffmpeg.exe"
    if target.exists() and not args.force:
        print(f"Already present: {target}")
        return 0

    with tempfile.TemporaryDirectory() as temp:
        archive_path = Path(temp) / "ffmpeg.zip"
        download(args.url, archive_path)
        extract(archive_path, root)

    if not target.exists():
        print("ffmpeg.exe was not found in the archive")
        return 1
    print(f"Done: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
