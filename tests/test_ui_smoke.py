from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")


class DummySettings:
    language = "zh"
    theme = "system"
    quality = 85
    preset = "balanced"
    custom_output_dir = ""


def test_main_window_smoke(qapp, tmp_path):
    from PIL import Image

    from app import i18n
    from app.ui.main_window import MainWindow

    i18n.set_language("zh")
    image_path = tmp_path / "photo.png"
    Image.new("RGB", (32, 24), "green").save(image_path)
    text_path = tmp_path / "note.md"
    text_path.write_text("# Hello\n", encoding="utf-8")

    window = MainWindow(DummySettings())
    try:
        window.add_paths([str(image_path), str(text_path)])
        assert len(window.entries) == 2
        assert len(window.cards) == 2
        assert window.start_button.isEnabled()
        for card in window.cards.values():
            assert card.selected_formats()
    finally:
        window.close()

    window.deleteLater()


def test_language_switch(qapp):
    from app import i18n
    from app.ui.main_window import MainWindow

    i18n.set_language("en")
    window = MainWindow(DummySettings())
    try:
        assert window.windowTitle() == "File Format Converter"
        assert window.action_add_files.text() == "Add files"
        i18n.set_language("zh")
        window.retranslate()
        assert window.windowTitle() == "格式转换小工具"
        assert window.action_add_files.text() == "添加文件"
    finally:
        window.close()
        i18n.set_language("zh")
    window.deleteLater()
