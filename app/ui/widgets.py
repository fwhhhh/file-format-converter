"""Reusable widgets: elided label and the drag & drop file list."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QSizePolicy,
)


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
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.setWordWrap(False)
        self.setUniformItemSizes(True)
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
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = self.viewport().rect().adjusted(5, 5, -5, -5)
            pen = QPen(self.palette().color(QPalette.ColorRole.Mid))
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, 8, 8)
            if self.count() == 0:
                painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
                font = self.font()
                font.setPointSize(font.pointSize() + 1)
                painter.setFont(font)
                painter.drawText(
                    rect,
                    int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap),
                    self._hint,
                )
