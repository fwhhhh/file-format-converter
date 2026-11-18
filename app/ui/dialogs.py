"""Dialogs: output location, settings, engine status and about."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
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
    QSizePolicy,
    QSlider,
    QVBoxLayout,
)

from .. import AUTHOR, AUTHOR_EMAIL, GITHUB_URL, __version__
from ..core.utils import resource_path
from ..engines import status_entries
from ..i18n import tr
from ..settings import Settings
from . import style

_OFFICE_URL = (
    "https://www.microsoft.com/microsoft-365/buy/compare-all-microsoft-365-products"
)

_INSTALL_URLS = {
    "pandoc": "https://pandoc.org/installing.html",
    "libreoffice": "https://www.libreoffice.org/download/",
    "calibre": "https://calibre-ebook.com/download",
    "word": _OFFICE_URL,
    "excel": _OFFICE_URL,
    "powerpoint": _OFFICE_URL,
    "ocr": "https://github.com/UB-Mannheim/tesseract/wiki",
}


def _link(url: str, text: str) -> str:
    color = style.current_colors().accent
    return f'<a href="{url}" style="color: {color}; text-decoration: none;">{text}</a>'


class OutputDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle(tr("output_title"))
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 18)
        layout.setSpacing(14)

        self.same_radio = QRadioButton(tr("output_same"), self)
        self.custom_radio = QRadioButton(tr("output_custom"), self)
        self.same_radio.setChecked(True)
        layout.addWidget(self.same_radio)

        custom_row = QHBoxLayout()
        custom_row.setSpacing(10)
        custom_row.addWidget(self.custom_radio)
        self.path_edit = QLineEdit(settings.custom_output_dir, self)
        self.path_edit.setEnabled(False)
        self.browse_button = QPushButton(tr("browse"), self)
        self.browse_button.setEnabled(False)
        custom_row.addWidget(self.path_edit, 1)
        custom_row.addWidget(self.browse_button)
        layout.addLayout(custom_row)
        layout.addSpacing(4)

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
        self.setMinimumWidth(460)

        form = QFormLayout(self)
        form.setContentsMargins(26, 22, 26, 18)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(14)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        quality_row = QHBoxLayout()
        quality_row.setSpacing(12)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(settings.quality)
        self.quality_value = QLabel(str(settings.quality), self)
        self.quality_value.setMinimumWidth(32)
        self.quality_value.setObjectName("Muted")
        quality_row.addWidget(self.quality_slider, 1)
        quality_row.addWidget(self.quality_value)
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

        form.addRow(self._make_buttons())

    def _make_buttons(self) -> QDialogButtonBox:
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        return buttons

    def accept(self) -> None:
        self.settings.quality = self.quality_slider.value()
        self.settings.preset = str(self.preset_combo.currentData())
        self.settings.language = str(self.language_combo.currentData())
        self.settings.theme = str(self.theme_combo.currentData())
        super().accept()


class EngineStatusDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("engines_title"))
        self.setModal(True)
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 18)
        layout.setSpacing(9)
        for key, label_key, available in status_entries():
            label = QLabel(self)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setOpenExternalLinks(True)
            if available:
                label.setProperty("kind", "ok")
                label.setText(f"✓  {tr(label_key)} · {tr('engine_available')}")
            else:
                label.setProperty("kind", "missing")
                url = _INSTALL_URLS.get(key)
                if url:
                    label.setText(
                        f"✗  {tr(label_key)} · {tr('engine_missing')} · "
                        f"{_link(url, tr('download'))}"
                    )
                else:
                    label.setText(f"✗  {tr(label_key)} · {tr('engine_missing')}")
            layout.addWidget(label)

        layout.addSpacing(4)
        note = QLabel(tr("engine_future_note"), self)
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        hint = QLabel(tr("engine_hint_missing"), self)
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        close_button.setText(tr("close"))
        close_button.setObjectName("Primary")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about"))
        self.setModal(True)
        self.setFixedWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 22)
        layout.setSpacing(8)

        self.icon_label = QLabel(self)
        pixmap = QIcon(str(resource_path("assets/app.ico"))).pixmap(56, 56)
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        title = QLabel(tr("app_title"), self)
        title.setObjectName("AboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel(f"v{__version__}", self)
        version.setObjectName("Muted")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        author = QLabel(AUTHOR, self)
        author.setObjectName("AuthorPill")
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        author_row = QHBoxLayout()
        author_row.addStretch(1)
        author_row.addWidget(author)
        author_row.addStretch(1)
        layout.addSpacing(4)
        layout.addLayout(author_row)
        layout.addSpacing(6)

        muted = style.current_colors().text_muted
        github_line = QLabel(
            f'<span style="color: {muted};">{tr("github_label")} · </span>'
            f"{_link(GITHUB_URL, GITHUB_URL)}",
            self,
        )
        github_line.setTextFormat(Qt.TextFormat.RichText)
        github_line.setOpenExternalLinks(True)
        github_line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(github_line)

        email_line = QLabel(
            f'<span style="color: {muted};">{tr("email_label")} · </span>'
            f"{_link(f'mailto:{AUTHOR_EMAIL}', AUTHOR_EMAIL)}",
            self,
        )
        email_line.setTextFormat(Qt.TextFormat.RichText)
        email_line.setOpenExternalLinks(True)
        email_line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(email_line)

        layout.addSpacing(8)
        description = QLabel(tr("about_text"), self)
        description.setObjectName("Muted")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        layout.addSpacing(10)
        close_button = QPushButton(tr("close"), self)
        close_button.setObjectName("Primary")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setMinimumWidth(110)
        close_button.clicked.connect(self.accept)
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_row.addWidget(close_button)
        close_row.addStretch(1)
        layout.addLayout(close_row)
