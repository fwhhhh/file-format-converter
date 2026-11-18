from __future__ import annotations

import time

import pytest

from app.engines.office import find_office_exe

pytest.importorskip("PySide6")


class DummySettings:
    language = "zh"
    theme = "light"
    quality = 85
    preset = "balanced"
    custom_output_dir = ""
    pdf_dpi = 144


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
        assert window.progress_text.text() == "2/2"
        assert window.start_button.isEnabled()
    finally:
        window.close()
    window.deleteLater()


@pytest.mark.skipif(find_office_exe("word") is None, reason="Microsoft Word missing")
def test_pdf_to_png_zip_flow(qapp, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QDialog

    from app import i18n
    from app.engines import engine_for
    from app.main import _write_minimal_docx
    from app.ui import main_window as window_module

    i18n.set_language("zh")
    docx = tmp_path / "sample.docx"
    _write_minimal_docx(docx)
    pdf = tmp_path / "sample.pdf"
    engine_for("docx", "pdf").convert(
        docx, pdf, {"target_format": "pdf", "source_format": "docx"}
    )
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    class FakeOutputDialog:
        def __init__(self, settings, parent=None):
            self.settings = settings

        def exec(self):
            return QDialog.DialogCode.Accepted

        def custom_folder(self):
            return output_dir

    monkeypatch.setattr(window_module, "OutputDialog", FakeOutputDialog)
    window = window_module.MainWindow(DummySettings())
    try:
        window.add_paths([str(pdf)])
        card = window.cards[1]
        assert "png" in card.chips
        card.set_selected_formats({"png"})
        window.start_conversion()

        deadline = time.time() + 60
        while window.running and time.time() < deadline:
            qapp.processEvents()
            time.sleep(0.01)
        qapp.processEvents()

        assert not window.running
        outputs = list(output_dir.iterdir())
        assert [path.name for path in outputs] == ["sample_png.zip"]
        assert window.progress_text.text() == "1/1"
    finally:
        window.close()
    window.deleteLater()
