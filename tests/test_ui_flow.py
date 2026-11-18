from __future__ import annotations

import time

import pytest

pytest.importorskip("PySide6")


class DummySettings:
    language = "zh"
    theme = "light"
    quality = 85
    preset = "balanced"
    custom_output_dir = ""


def test_conversion_flow(qapp, tmp_path, monkeypatch):
    from PIL import Image
    from PySide6.QtWidgets import QDialog

    from app import i18n
    from app.ui import main_window as window_module

    i18n.set_language("zh")
    source = tmp_path / "photo.png"
    Image.new("RGB", (40, 30), "teal").save(source)
    output_dir = tmp_path / "out"

    class FakeOutputDialog:
        def __init__(self, settings, parent=None):
            self.settings = settings

        def exec(self):
            return QDialog.DialogCode.Accepted

        def custom_folder(self):
            return output_dir

    monkeypatch.setattr(window_module, "OutputDialog", FakeOutputDialog)
    output_dir.mkdir(parents=True, exist_ok=True)
    window = window_module.MainWindow(DummySettings())
    try:
        window.add_paths([str(source)])
        card = window.cards[1]
        card.set_selected_formats({"jpg", "webp"})
        window.start_conversion()

        deadline = time.time() + 30
        while window.running and time.time() < deadline:
            qapp.processEvents()
            time.sleep(0.01)
        qapp.processEvents()

        assert not window.running
        outputs = sorted(path.name for path in output_dir.iterdir())
        assert outputs == ["photo.jpg", "photo.webp"]
        assert window.progress.value() == 1000
        assert window.progress.format() == "2/2"
        assert window.start_button.isEnabled()
    finally:
        window.close()
    window.deleteLater()
