"""Reusable widgets: elided label and the drag & drop file list."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QSizePolicy,
)

from . import style


class ElidedLabel(QLabel):
    """QLabel that shortens long text with an ellipsis instead of growing."""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        metrics = painter.fontMetrics()
        elided = metrics.elidedText(self.text(), Qt.TextElideMode.ElideMiddle, self.width())
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(self.contentsRect(), int(self.alignment()), elided)


class FileDropList(QListWidget):
    paths_dropped = Signal(list)
    remove_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("FileList")
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.setWordWrap(False)
        self.setUniformItemSizes(True)
        self.setIconSize(QSize(22, 22))
        self.setSpacing(2)
        self._hint = ""
        self._drag_hover = False

    def set_hint(self, text: str) -> None:
        self._hint = text
        self.viewport().update()

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            self._drag_hover = True
            self.viewport().update()
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._drag_hover = False
        self.viewport().update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        self._drag_hover = False
        self.viewport().update()
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()
            return
        event.ignore()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_requested.emit()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self.count() == 0 or self._drag_hover:
            colors = style.current_colors()
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = self.viewport().rect().adjusted(6, 6, -6, -6)
            border = QColor(colors.accent)
            if not self._drag_hover:
                border.setAlpha(130)
            pen = QPen(border)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidthF(1.4)
            painter.setPen(pen)
            fill = QColor(colors.accent_soft)
            fill.setAlpha(160 if self._drag_hover else 120)
            painter.setBrush(fill)
            painter.drawRoundedRect(rect, 12, 12)
            if self.count() == 0:
                painter.setPen(QColor(colors.text_muted))
                font = self.font()
                font.setPointSize(font.pointSize() + 1)
                painter.setFont(font)
                painter.drawText(
                    rect,
                    int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap),
                    self._hint,
                )
