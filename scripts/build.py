"""Build the portable Windows package with PyInstaller.

Usage:
    python scripts/build.py            # slim build, detects external tools
    python scripts/build.py --full     # bundles Pandoc, Tesseract, LibreOffice, Calibre
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import PyInstaller.__main__


def _copy_tool(source: Path, destination: Path, label: str) -> None:
    started = time.time()
    print(f"Bundling {label}: {source}")
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    elapsed = time.time() - started
    print(f"  done in {elapsed:.1f}s")


def _bundle_full_tools(root: Path, stage_vendor: Path) -> bool:
    sys.path.insert(0, str(root))
    from app.engines.calibre import find_ebook_convert
    from app.engines.libreoffice import find_soffice
    from app.engines.pandoc import find_pandoc
    from app.engines.ocr import find_tesseract

    pandoc = find_pandoc()
    tesseract = find_tesseract()
    soffice = find_soffice()
    ebook_convert = find_ebook_convert()
    missing = []
    if not pandoc:
        missing.append("Pandoc")
    if not tesseract:
        missing.append("Tesseract")
    if not soffice:
        missing.append("LibreOffice")
    if not ebook_convert:
        missing.append("Calibre")
    if missing:
        print("Cannot build the full package, missing: " + ", ".join(missing))
        return False

    pandoc_path = Path(pandoc)
    _copy_tool(pandoc_path, stage_vendor / "pandoc" / "pandoc.exe", "Pandoc")
    for license_name in ("COPYING.txt", "COPYRIGHT.txt", "LICENSE.txt"):
        license_path = pandoc_path.parent / license_name
        if license_path.exists():
            shutil.copy2(license_path, stage_vendor / "pandoc" / license_name)

    _copy_tool(
        Path(tesseract).parent,
        stage_vendor / "tesseract",
        "Tesseract OCR",
    )
    _copy_tool(
        Path(soffice).parent.parent,
        stage_vendor / "libreoffice",
        "LibreOffice",
    )
    _copy_tool(
        Path(ebook_convert).parent,
        stage_vendor / "calibre",
        "Calibre",
    )
    return True


def trim_dist(root: Path, app_name: str) -> None:
    """Remove Qt/PySide components that this app never uses."""
    internal = root / "dist" / app_name / "_internal"
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
    parser = argparse.ArgumentParser(description="Build the portable package")
    parser.add_argument(
        "--full",
        action="store_true",
        help="bundle Pandoc, Tesseract, LibreOffice and Calibre",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    app_name = "FileFormatConverter-Full" if args.full else "FileFormatConverter"
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
        app_name,
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
        if args.full:
            if not _bundle_full_tools(root, stage_vendor):
                return 1
            copied_vendor = True
        if copied_vendor:
            arguments += ["--add-data", f"{stage_vendor}{separator}vendor"]
        arguments.append(str(root / "run.py"))
        PyInstaller.__main__.run(arguments)
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    trim_dist(root, app_name)
    dist_root = root / "dist" / app_name
    for source, name in (
        (root / "LICENSE", "LICENSE.txt"),
        (root / "docs" / "THIRD_PARTY.md", "THIRD_PARTY.md"),
        (root / "README.md", "README.md"),
        (root / "README.zh-CN.md", "README.zh-CN.md"),
    ):
        if source.exists():
            try:
                shutil.copy2(source, dist_root / name)
            except OSError:
                pass
    print(f"Done. Output: dist/{app_name}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
