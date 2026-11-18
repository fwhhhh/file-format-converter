"""Dialogs: output location, settings, engine status."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
)

from ..engines import status_entries
from ..i18n import tr
from ..settings import Settings


class OutputDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle(tr("output_title"))
        self.setModal(True)

        layout = QVBoxLayout(self)
        self.same_radio = QRadioButton(tr("output_same"), self)
        self.custom_radio = QRadioButton(tr("output_custom"), self)
        self.same_radio.setChecked(True)
        layout.addWidget(self.same_radio)

        custom_row = QHBoxLayout()
        custom_row.addWidget(self.custom_radio)
        self.path_edit = QLineEdit(settings.custom_output_dir, self)
        self.path_edit.setEnabled(False)
        self.browse_button = QPushButton(tr("browse"), self)
        self.browse_button.setEnabled(False)
        custom_row.addWidget(self.path_edit, 1)
        custom_row.addWidget(self.browse_button)
        layout.addLayout(custom_row)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("ok"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        layout.addWidget(self.buttons)

        self.custom_radio.toggled.connect(self._update_enabled)
        self.browse_button.clicked.connect(self._browse)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def _update_enabled(self, checked: bool) -> None:
        self.path_edit.setEnabled(checked)
        self.browse_button.setEnabled(checked)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("output_custom"), self.path_edit.text())
        if folder:
            self.path_edit.setText(folder)

    def accept(self) -> None:
        if self.custom_radio.isChecked():
            text = self.path_edit.text().strip()
            if not text:
                QMessageBox.warning(self, tr("output_title"), tr("custom_dir_invalid", path=text))
                return
            folder = Path(text)
            try:
                folder.mkdir(parents=True, exist_ok=True)
            except OSError:
                QMessageBox.warning(
                    self, tr("output_title"), tr("custom_dir_create_failed", path=text)
                )
                return
            if not folder.is_dir():
                QMessageBox.warning(self, tr("output_title"), tr("custom_dir_invalid", path=text))
                return
            self.settings.custom_output_dir = str(folder)
        super().accept()

    def custom_folder(self) -> Path | None:
        if self.custom_radio.isChecked():
            return Path(self.path_edit.text().strip())
        return None


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle(tr("settings_title"))
        self.setModal(True)

        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        quality_row = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(settings.quality)
        self.quality_value = QLabel(str(settings.quality), self)
        self.quality_value.setMinimumWidth(28)
        quality_row.addWidget(self.quality_slider, 1)
        quality_row.addWidget(self.quality_value)
        self.quality_slider.valueChanged.connect(
            lambda value: self.quality_value.setText(str(value))
        )
        form.addRow(tr("quality"), quality_row)

        self.preset_combo = QComboBox(self)
        self.preset_combo.addItem(tr("preset_high"), "high")
        self.preset_combo.addItem(tr("preset_balanced"), "balanced")
        self.preset_combo.addItem(tr("preset_small"), "small")
        self.preset_combo.setCurrentIndex(
            max(0, self.preset_combo.findData(settings.preset))
        )
        form.addRow(tr("preset"), self.preset_combo)

        self.language_combo = QComboBox(self)
        self.language_combo.addItem("简体中文", "zh")
        self.language_combo.addItem("English", "en")
        self.language_combo.setCurrentIndex(
            max(0, self.language_combo.findData(settings.language))
        )
        form.addRow(tr("language"), self.language_combo)

        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem(tr("theme_system"), "system")
        self.theme_combo.addItem(tr("theme_light"), "light")
        self.theme_combo.addItem(tr("theme_dark"), "dark")
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(settings.theme)))
        form.addRow(tr("theme"), self.theme_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def accept(self) -> None:
        self.settings.quality = self.quality_slider.value()
        self.settings.preset = str(self.preset_combo.currentData())
        self.settings.language = str(self.language_combo.currentData())
        self.settings.theme = str(self.theme_combo.currentData())
        super().accept()


_INSTALL_URLS = {
    "pandoc": "https://pandoc.org/installing.html",
    "libreoffice": "https://www.libreoffice.org/download/",
    "calibre": "https://calibre-ebook.com/download",
}


class EngineStatusDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("engines_title"))
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        for key, label_key, available in status_entries():
            label = QLabel(self)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setOpenExternalLinks(True)
            if available:
                label.setText(f"✓  {tr(label_key)} · {tr('engine_available')}")
                label.setStyleSheet("color: #2e7d32;")
            else:
                url = _INSTALL_URLS.get(key)
                if url:
                    label.setText(
                        f"✗  {tr(label_key)} · {tr('engine_missing')} · "
                        f"<a href=\"{url}\">{tr('download')}</a>"
                    )
                else:
                    label.setText(f"✗  {tr(label_key)} · {tr('engine_missing')}")
                label.setForegroundRole(QPalette.ColorRole.PlaceholderText)
            layout.addWidget(label)

        note = QLabel(tr("engine_future_note"), self)
        note.setWordWrap(True)
        note.setForegroundRole(QPalette.ColorRole.PlaceholderText)
        layout.addWidget(note)

        hint = QLabel(tr("engine_hint_missing"), self)
        hint.setWordWrap(True)
        hint.setForegroundRole(QPalette.ColorRole.PlaceholderText)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(tr("close"))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
