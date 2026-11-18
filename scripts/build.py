"""Build the portable Windows package with PyInstaller.

Usage:
    python scripts/build.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import PyInstaller.__main__


def trim_dist(root: Path) -> None:
    """Remove Qt/PySide components that this app never uses.

    PyInstaller's PySide6 hook collects the FFmpeg backend DLLs of QtMultimedia
    (about 150 MiB) and several optional Qt modules.  None of them are imported
    by the application, so they are stripped from the package.
    """
    internal = root / "dist" / "FileFormatConverter" / "_internal"
    if not internal.exists():
        return
    targets: list[Path] = []
    for pattern in (
        "avcodec-*.dll",
        "avdevice-*.dll",
        "avfilter-*.dll",
        "avformat-*.dll",
        "avutil-*.dll",
        "swresample-*.dll",
        "swscale-*.dll",
    ):
        targets.extend(internal.glob(pattern))

    pyside = internal / "PySide6"
    for pattern in (
        "Qt6Qml*.dll",
        "Qt6Quick*.dll",
        "Qt6VirtualKeyboard.dll",
        "Qt6Pdf.dll",
        "opengl32sw.dll",
    ):
        targets.extend(pyside.glob(pattern))
    targets.append(pyside / "plugins" / "imageformats" / "qpdf.dll")

    removed = 0
    for path in targets:
        if not path.is_file():
            continue
        size = path.stat().st_size
        try:
            path.unlink()
        except OSError:
            continue
        removed += size

    for directory in (pyside / "plugins" / "platforminputcontexts",):
        if directory.is_dir():
            for item in directory.rglob("*"):
                if item.is_file():
                    removed += item.stat().st_size
            shutil.rmtree(directory, ignore_errors=True)

    print(f"Trimmed {removed / 1048576:.1f} MiB of unused components")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    icon = root / "assets" / "app.ico"
    if not icon.exists():
        print("Icon missing, generating it...")
        sys.path.insert(0, str(root / "scripts"))
        from make_icon import main as make_icon

        make_icon()

    ffmpeg = root / "vendor" / "ffmpeg" / "bin" / "ffmpeg.exe"
    if not ffmpeg.exists():
        print("WARNING: vendor/ffmpeg is missing; the package will not convert audio/video.")
        print("Run: python scripts/download_deps.py")

    separator = os.pathsep
    arguments = [
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "FileFormatConverter",
        "--icon",
        str(icon),
        "--add-data",
        f"{root / 'assets'}{separator}assets",
        "--add-data",
        f"{root / 'docs'}{separator}docs",
        "--add-data",
        f"{root / 'LICENSE'}{separator}.",
        "--collect-all",
        "pypdfium2",
        "--collect-all",
        "pypdfium2_raw",
    ]

    stage = Path(tempfile.mkdtemp(prefix="ffc_build_"))
    try:
        stage_vendor = stage / "vendor"
        copied_vendor = False
        for name in ("ffmpeg", "tessdata"):
            source = root / "vendor" / name
            if source.exists():
                shutil.copytree(
                    source,
                    stage_vendor / name,
                    ignore=shutil.ignore_patterns("*.zip"),
                )
                copied_vendor = True
        if copied_vendor:
            arguments += ["--add-data", f"{stage_vendor}{separator}vendor"]
        arguments.append(str(root / "run.py"))
        PyInstaller.__main__.run(arguments)
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    trim_dist(root)
    dist_root = root / "dist" / "FileFormatConverter"
    for source, name in (
        (root / "LICENSE", "LICENSE.txt"),
        (root / "docs" / "THIRD_PARTY.md", "THIRD_PARTY.md"),
    ):
        if source.exists():
            try:
                shutil.copy2(source, dist_root / name)
            except OSError:
                pass
    print("Done. Output: dist/FileFormatConverter/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
