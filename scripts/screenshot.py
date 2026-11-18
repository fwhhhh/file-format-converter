"""Create sample files and render screenshots of the main window.

Run with the project virtual environment:
    python scripts/screenshot.py --lang zh
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

if "--offscreen" in sys.argv:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from app import i18n  # noqa: E402
from app.core.utils import project_root  # noqa: E402
from app.engines.office import find_office_exe  # noqa: E402
from app.main import _write_minimal_docx  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402
from app.ui.theme import apply_theme  # noqa: E402


class DummySettings:
    language = "zh"
    theme = "system"
    quality = 85
    preset = "balanced"
    custom_output_dir = ""
    pdf_dpi = 144
    filename_suffix = ""


def create_samples(folder: Path) -> list[str]:
    from PIL import Image, ImageDraw

    width, height = 1280, 800
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / height
        draw.line(
            [(0, y), (width, y)],
            fill=(
                int(30 + 60 * ratio),
                int(90 + 90 * ratio),
                int(200 - 60 * ratio),
            ),
        )
    draw.ellipse([420, 200, 860, 640], fill=(255, 220, 120))
    photo = folder / "photo.png"
    image.save(photo)

    notes = folder / "notes.md"
    notes.write_text(
        "# 格式转换小工具\n\n"
        "拖入文件，勾选格式，开始转换。\n\n"
        "- 图片互转\n- 音视频互转\n- 压缩包互转\n",
        encoding="utf-8",
    )

    data = folder / "data.csv"
    with open(data, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "score"])
        writer.writerow(["Alice", "92"])
        writer.writerow(["Bob", "88"])

    archive = folder / "bundle.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("readme.txt", "hello")
        handle.writestr("src/main.c", "int main(void) { return 0; }")

    paths: list[str] = []
    if find_office_exe("word"):
        report = folder / "report.docx"
        _write_minimal_docx(report)
        paths.append(str(report))
    paths.append(str(photo))

    ffmpeg = project_root() / "vendor" / "ffmpeg" / "bin" / "ffmpeg.exe"
    if ffmpeg.exists():
        clip = folder / "clip.mp4"
        try:
            subprocess.run(
                [
                    str(ffmpeg),
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=duration=2:size=640x360:rate=15",
                    "-pix_fmt",
                    "yuv420p",
                    str(clip),
                ],
                check=True,
                creationflags=0x08000000,
            )
            paths.append(str(clip))
        except (OSError, subprocess.SubprocessError):
            pass
    paths.extend([str(notes), str(data), str(archive)])
    return paths


def _run_conversions(window: MainWindow, app: QApplication, output_dir: Path) -> None:
    from PySide6.QtWidgets import QDialog

    from app.ui import main_window as window_module

    class FakeOutputDialog:
        def __init__(self, settings, parent=None) -> None:
            pass

        def exec(self) -> int:
            return int(QDialog.DialogCode.Accepted)

        def custom_folder(self) -> Path:
            return output_dir

    original = window_module.OutputDialog
    window_module.OutputDialog = FakeOutputDialog
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        window.start_conversion()
        deadline = time.time() + 180
        while window.running and time.time() < deadline:
            app.processEvents()
            time.sleep(0.02)
        for _ in range(10):
            app.processEvents()
            time.sleep(0.02)
    finally:
        window_module.OutputDialog = original


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="zh", choices=["zh", "en"])
    parser.add_argument("--theme", default="light", choices=["system", "light", "dark"])
    parser.add_argument("--out", default="")
    parser.add_argument("--with-results", action="store_true")
    parser.add_argument("--offscreen", action="store_true")
    args = parser.parse_args()

    app = QApplication.instance() or QApplication([])
    i18n.set_language(args.lang)
    apply_theme(app, args.theme)

    window = MainWindow(DummySettings())
    window.setWindowTitle(i18n.tr("app_title"))
    window.resize(1040, 690)
    window.show()
    app.processEvents()

    temp_dir = Path(tempfile.mkdtemp(prefix="ffc_shot_"))
    try:
        samples = create_samples(temp_dir)
        window.add_paths(samples)
        app.processEvents()
        app.processEvents()

        if args.with_results:
            _run_conversions(window, app, temp_dir / "out")
            for index, card in enumerate(window.cards.values()):
                if index > 0:
                    card.toggle_button.click()
            app.processEvents()

        window.file_list.clearSelection()
        window.file_list.setCurrentRow(-1)
        window.resize(1040, 690)
        app.processEvents()

        docs = ROOT / "docs"
        docs.mkdir(exist_ok=True)
        output = Path(args.out) if args.out else docs / f"screenshot-{args.lang}.png"
        window.grab().save(str(output))
        print(f"Saved {output}")
    finally:
        window.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
