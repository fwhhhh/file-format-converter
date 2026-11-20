"""Build the portable Windows package with PyInstaller.

Usage:
    python scripts/build.py            # slim build, detects external tools
    python scripts/build.py --full     # bundles Pandoc, Tesseract, LibreOffice, Calibre
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

import PyInstaller.__main__


def remove_tree(path: Path) -> None:
    """Delete a build folder even when copied tools are read-only."""
    if not path.exists():
        return
    for item in [path, *path.rglob("*")]:
        try:
            item.chmod(stat.S_IWRITE)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        raise OSError(f"Cannot remove {path}")


def _full_tool_sources(root: Path) -> dict[str, Path] | None:
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
        return None
    return {
        "pandoc": Path(pandoc),
        "tesseract": Path(tesseract).parent,
        "libreoffice": Path(soffice).parent.parent,
        "calibre": Path(ebook_convert).parent,
    }


def _copy_full_tools(
    root: Path,
    app_name: str,
    sources: dict[str, Path],
) -> None:
    """Copy document tools after PyInstaller finishes.

    Copying them through ``--add-data`` makes PyInstaller inspect their DLLs
    (Calibre ships its own Qt/Python runtimes) and pull them into the
    application root, which conflicts with PySide6.  A plain directory copy
    after the build keeps them isolated under ``vendor``.
    """
    vendor = root / "dist" / app_name / "_internal" / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)

    pandoc_dir = vendor / "pandoc"
    pandoc_dir.mkdir(parents=True, exist_ok=True)
    pandoc_exe = sources["pandoc"]
    shutil.copy2(pandoc_exe, pandoc_dir / "pandoc.exe")
    for license_name in ("COPYING.txt", "COPYRIGHT.txt", "LICENSE.txt"):
        license_path = pandoc_exe.parent / license_name
        if license_path.exists():
            shutil.copy2(license_path, pandoc_dir / license_name)

    for key, name in (
        ("tesseract", "tesseract"),
        ("libreoffice", "libreoffice"),
        ("calibre", "calibre"),
    ):
        target = vendor / name
        if target.exists():
            remove_tree(target)
        print(f"Copying bundled {name}...")
        shutil.copytree(sources[key], target)
    print("Document tools copied into the package")


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
    full_tools: dict[str, Path] | None = None
    if args.full:
        full_tools = _full_tool_sources(root)
        if full_tools is None:
            return 1
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
        remove_tree(root / "dist" / app_name)
        PyInstaller.__main__.run(arguments)
    finally:
        remove_tree(stage)

    trim_dist(root, app_name)
    if args.full and full_tools is not None:
        _copy_full_tools(root, app_name, full_tools)
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
