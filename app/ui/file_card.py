"""Collapsible card that configures the target formats of one file."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileInfo, Qt, Signal
from PySide6.QtWidgets import (
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..core import formats
from ..core.models import Entry
from ..core.utils import format_duration, human_size, open_path
from ..i18n import tr, trn
from .flow_layout import FlowLayout
from .widgets import ElidedLabel

_ICON_PROVIDER: QFileIconProvider | None = None


def _icon_provider() -> QFileIconProvider:
    global _ICON_PROVIDER
    if _ICON_PROVIDER is None:
        _ICON_PROVIDER = QFileIconProvider()
    return _ICON_PROVIDER


class ResultRow(QFrame):
    def __init__(self, fmt: str, dst: Path, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ResultRow")
        self.fmt = fmt
        self.dst = dst
        self.kind = "idle"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(8)

        self.status_label = QLabel("·", self)
        self.status_label.setFixedWidth(16)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setVisible(False)
        self.name_label = ElidedLabel(dst.name, self)
        self.size_label = QLabel("", self)
        self.size_label.setObjectName("Muted")
        self.open_button = QPushButton(tr("open"), self)
        self.open_button.setObjectName("LinkGhost")
        self.open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_button.setToolTip(tr("open_folder"))
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self._open_folder)

        layout.addWidget(self.status_label)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.size_label)
        layout.addWidget(self.open_button)
        self._set_idle()

    def _open_folder(self) -> None:
        open_path(self.dst.parent)

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _set_status(self, symbol: str, kind: str, tooltip: str = "") -> None:
        self.kind = kind
        self.status_label.setText(symbol)
        self.status_label.setProperty("kind", kind)
        self._repolish(self.status_label)
        self.status_label.setToolTip(tooltip)

    def _set_idle(self) -> None:
        self._set_status("·", "idle")
        self.icon_label.setVisible(False)
        self.name_label.setText(self.dst.name)
        self.name_label.setToolTip(str(self.dst))
        self.size_label.setText("")
        self.open_button.setEnabled(False)

    def set_waiting(self) -> None:
        self._set_idle()
        self._set_status("·", "idle", tr("waiting"))

    def set_running(self) -> None:
        self._set_idle()
        self._set_status("…", "idle", tr("converting"))

    def set_done(self, path: Path) -> None:
        self.dst = path
        self._set_status("✓", "ok", str(path))
        icon = _icon_provider().icon(QFileInfo(str(path)))
        self.icon_label.setPixmap(icon.pixmap(18, 18))
        self.icon_label.setToolTip(str(path))
        self.icon_label.setVisible(True)
        self.name_label.setText(path.name)
        self.name_label.setToolTip(str(path))
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        self.size_label.setText(human_size(size))
        self.open_button.setEnabled(True)

    def set_failed(self, message: str) -> None:
        self._set_status("✗", "fail", message)
        self.icon_label.setVisible(False)
        self.name_label.setText(f"{self.dst.name} · {tr('failed')}")
        self.name_label.setToolTip(message)
        self.size_label.setText("")
        self.open_button.setEnabled(False)

    def retranslate(self) -> None:
        self.open_button.setText(tr("open"))
        self.open_button.setToolTip(tr("open_folder"))
        self._repolish(self.status_label)


class FileCard(QFrame):
    selection_changed = Signal()
    apply_requested = Signal(int, set)

    def __init__(self, entry: Entry, parent=None) -> None:
        super().__init__(parent)
        self.entry = entry
        self.expanded = True
        self.selected: set[str] = set()
        self.chips: dict[str, QPushButton] = {}
        self.result_rows: dict[str, ResultRow] = {}
        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._build()
        default = formats.default_target(entry.ext, entry.targets)
        if default:
            self.chips[default].setChecked(True)
        self._sync_selection()

    # ------------------------------------------------------------------ UI

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.toggle_button = QToolButton(self)
        self.toggle_button.setObjectName("CardToggle")
        self.toggle_button.setText("▾")
        self.toggle_button.setAutoRaise(True)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.clicked.connect(self._toggle)

        self.file_icon = QLabel(self)
        self.file_icon.setFixedSize(20, 20)
        icon = _icon_provider().icon(QFileInfo(str(self.entry.path)))
        pixmap = icon.pixmap(20, 20)
        if not pixmap.isNull():
            self.file_icon.setPixmap(pixmap)

        self.name_label = ElidedLabel(self.entry.path.name, self)
        self.name_label.setObjectName("CardTitle")
        self.name_label.setToolTip(str(self.entry.path))
        self.meta_label = QLabel("", self)
        self.meta_label.setObjectName("Muted")
        self.apply_button = QPushButton(tr("apply_same"), self)
        self.apply_button.setObjectName("LinkGhost")
        self.apply_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_button.setVisible(False)
        self.apply_button.clicked.connect(
            lambda: self.apply_requested.emit(self.entry.entry_id, set(self.selected))
        )
        header.addWidget(self.toggle_button)
        header.addWidget(self.file_icon)
        header.addWidget(self.name_label, 1)
        header.addWidget(self.meta_label)
        header.addWidget(self.apply_button)
        outer.addLayout(header)

        self.body = QWidget(self)
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(28, 0, 0, 0)
        body_layout.setSpacing(10)
        self.targets_label = QLabel(tr("targets"), self.body)
        self.targets_label.setObjectName("Muted")
        body_layout.addWidget(self.targets_label)

        self.flow = FlowLayout(None, 0, 8)
        for fmt in self.entry.targets:
            chip = QPushButton(formats.display(fmt), self.body)
            chip.setObjectName("Chip")
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            chip.toggled.connect(lambda checked, f=fmt: self._on_chip(f, checked))
            self.chips[fmt] = chip
            self.flow.addWidget(chip)
        body_layout.addLayout(self.flow)

        self.result_label = QLabel(tr("result"), self.body)
        self.result_label.setObjectName("Muted")
        self.result_box = QWidget(self.body)
        self.result_layout = QVBoxLayout(self.result_box)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(6)
        body_layout.addWidget(self.result_label)
        body_layout.addWidget(self.result_box)
        self.result_label.setVisible(False)
        self.result_box.setVisible(False)

        outer.addWidget(self.body)
        self._update_meta()

    def _toggle(self) -> None:
        self.expanded = not self.expanded
        self.body.setVisible(self.expanded)
        self.toggle_button.setText("▾" if self.expanded else "▸")
        self._update_meta()

    def _on_chip(self, fmt: str, checked: bool) -> None:
        if checked:
            self.selected.add(fmt)
        else:
            self.selected.discard(fmt)
            self._remove_result_row(fmt)
        self._update_meta()
        self.selection_changed.emit()

    def _sync_selection(self) -> None:
        self.selected = {fmt for fmt, chip in self.chips.items() if chip.isChecked()}

    def _update_meta(self) -> None:
        if not self.expanded:
            text = trn("selected_one", "selected_many", len(self.selected))
            self.meta_label.setText(text)
            self.meta_label.setToolTip(text)
            return
        size_text = human_size(self.entry.size)
        meta = self.entry.meta or {}
        group = formats.group_of(self.entry.ext)
        if group == "image" and meta.get("width") and meta.get("height"):
            text = tr("image_info", w=meta["width"], h=meta["height"], size=size_text)
        elif group in ("video", "audio") and meta.get("duration"):
            text = tr("media_info", duration=format_duration(meta["duration"]), size=size_text)
        else:
            text = size_text
        self.meta_label.setText(text)
        self.meta_label.setToolTip(text)

    # ---------------------------------------------------------- public API

    def selected_formats(self) -> set[str]:
        return set(self.selected)

    def set_selected_formats(self, formats_set: set[str]) -> None:
        for fmt, chip in self.chips.items():
            chip.blockSignals(True)
            chip.setChecked(fmt in formats_set)
            chip.blockSignals(False)
        self._sync_selection()
        self._update_meta()
        self.selection_changed.emit()

    def set_apply_visible(self, visible: bool) -> None:
        self.apply_button.setVisible(visible)

    def prepare_results(self, destinations: dict[str, Path]) -> None:
        self._clear_results()
        for fmt in self.entry.targets:
            if fmt not in destinations:
                continue
            row = ResultRow(fmt, destinations[fmt], self.result_box)
            self.result_layout.addWidget(row)
            self.result_rows[fmt] = row
        has_rows = bool(self.result_rows)
        self.result_label.setVisible(has_rows)
        self.result_box.setVisible(has_rows)

    def set_running(self, fmt: str) -> None:
        row = self.result_rows.get(fmt)
        if row is not None:
            row.set_running()

    def set_result(self, fmt: str, path: Path) -> None:
        row = self.result_rows.get(fmt)
        if row is not None:
            row.set_done(path)

    def set_failed(self, fmt: str, message: str) -> None:
        row = self.result_rows.get(fmt)
        if row is not None:
            row.set_failed(message)

    def retranslate(self) -> None:
        self.targets_label.setText(tr("targets"))
        self.result_label.setText(tr("result"))
        self.apply_button.setText(tr("apply_same"))
        for row in self.result_rows.values():
            row.retranslate()
        self._update_meta()

    # ------------------------------------------------------------- private

    def _clear_results(self) -> None:
        for row in self.result_rows.values():
            self.result_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self.result_rows.clear()
        self.result_label.setVisible(False)
        self.result_box.setVisible(False)

    def _remove_result_row(self, fmt: str) -> None:
        row = self.result_rows.pop(fmt, None)
        if row is None:
            return
        self.result_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        has_rows = bool(self.result_rows)
        self.result_label.setVisible(has_rows)
        self.result_box.setVisible(has_rows)
