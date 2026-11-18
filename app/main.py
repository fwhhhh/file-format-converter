"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from . import __version__, i18n
from .core.utils import resource_path


def run_selftest() -> int:
    """Hidden ``--selftest`` mode used to verify a packaged build."""
    import csv
    import struct
    import tempfile
    import wave
    import zipfile

    temp_root = Path(tempfile.mkdtemp(prefix="ffc_selftest_"))
    lines: list[str] = []
    cases: list[tuple[Path, str]] = []
    try:
        from PIL import Image

        image_path = temp_root / "image.png"
        Image.new("RGB", (64, 48), "red").save(image_path)
        cases.extend([(image_path, "jpg"), (image_path, "webp"), (image_path, "pdf")])

        md_path = temp_root / "note.md"
        md_path.write_text("# Title\n\nHello **world**\n", encoding="utf-8")
        cases.append((md_path, "html"))

        csv_path = temp_root / "data.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows([["a", "b"], [1, 2]])
        cases.append((csv_path, "xlsx"))

        zip_path = temp_root / "data.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("a.txt", "hello")
        cases.append((zip_path, "7z"))

        wav_path = temp_root / "tone.wav"
        with wave.open(str(wav_path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(22050)
            handle.writeframes(b"".join(struct.pack("<h", 2000) for _ in range(4410)))
        cases.append((wav_path, "mp3"))

        try:
            import pillow_heif

            pillow_heif.register_heif_opener()
            heic_path = temp_root / "photo.heic"
            Image.new("RGB", (32, 24), "orange").save(heic_path, format="HEIF")
            cases.append((heic_path, "png"))
        except Exception:
            lines.append("SKIP HEIC support")

        from .core import detect
        from .engines import engine_for

        for source, target in cases:
            source_ext = detect.sniff_ext(source)
            engine = engine_for(source_ext, target)
            destination = temp_root / f"{source.stem}_out.{target}"
            try:
                if engine is None:
                    raise RuntimeError(f"no engine for {source_ext} -> {target}")
                engine.convert(source, destination, {"quality": 85, "preset": "balanced"})
                lines.append(f"OK   {source.name} -> {target} ({destination.stat().st_size} bytes)")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"FAIL {source.name} -> {target}: {exc}")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"FAIL setup: {exc}")
    finally:
        import shutil

        shutil.rmtree(temp_root, ignore_errors=True)

    if getattr(sys, "frozen", False):
        output = Path(sys.executable).parent / "selftest.txt"
    else:
        output = Path.cwd() / "selftest.txt"
    try:
        output.write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        output = Path(tempfile.gettempdir()) / "ffc_selftest.txt"
        output.write_text("\n".join(lines), encoding="utf-8")
    return 0 if lines and all(line.startswith(("OK", "SKIP")) for line in lines) else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from .settings import Settings
    from .ui.main_window import MainWindow
    from .ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("FileFormatConverter")
    app.setOrganizationName("FileFormatConverter")
    app.setApplicationVersion(__version__)

    icon_path = resource_path("assets/app.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    settings = Settings()
    i18n.set_language(settings.language)
    apply_theme(app, settings.theme)

    def on_system_theme_changed(*_args: object) -> None:
        if settings.theme == "system":
            apply_theme(app, "system")

    try:
        app.styleHints().colorSchemeChanged.connect(on_system_theme_changed)
    except (AttributeError, TypeError):
        pass

    window = MainWindow(settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
