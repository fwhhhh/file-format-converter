"""PDF toolbox dialog: merge, split, extract and image/PDF conversion."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core import pdf_tools, utils
from ..i18n import tr
from ..settings import Settings

_PDF_FILTER = "PDF (*.pdf)"
_IMAGE_FILTER = (
    "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.heic *.ppm)"
)


@contextmanager
def _busy():
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


class PdfToolsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle(tr("pdf_tools"))
        self.setModal(True)
        self.setMinimumSize(660, 540)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_merge_tab(), tr("pdf_merge"))
        self.tabs.addTab(self._build_split_tab(), tr("pdf_split"))
        self.tabs.addTab(self._build_extract_tab(), tr("pdf_extract"))
        self.tabs.addTab(self._build_images_pdf_tab(), tr("pdf_images_to_pdf"))
        self.tabs.addTab(self._build_pdf_images_tab(), tr("pdf_to_images"))
        layout.addWidget(self.tabs, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close_button = QPushButton(tr("close"), self)
        close_button.setObjectName("Primary")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setMinimumWidth(110)
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    # --------------------------------------------------------------- helpers

    def _ghost(self, text: str, callback) -> QPushButton:
        button = QPushButton(text, self)
        button.setObjectName("Ghost")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        return button

    def _primary(self, text: str, callback) -> QPushButton:
        button = QPushButton(text, self)
        button.setObjectName("Primary")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumWidth(110)
        button.clicked.connect(callback)
        return button

    def _file_row(self, label_text: str, line_edit: QLineEdit, picker) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label_text, self))
        line_edit.setPlaceholderText("")
        row.addWidget(line_edit, 1)
        browse = self._ghost(tr("browse"), picker)
        row.addWidget(browse)
        return row

    def _action_row(self, button: QPushButton) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(button)
        return row

    def _pick_open(self, title: str, filters: str) -> str:
        path, _ = QFileDialog.getOpenFileName(self, title, "", filters)
        return path

    def _pick_save(self, title: str, filters: str, suggestion: str) -> str:
        path, _ = QFileDialog.getSaveFileName(self, title, suggestion, filters)
        return path

    def _pick_dir(self, title: str) -> str:
        return QFileDialog.getExistingDirectory(self, title)

    def _unique_output(self, raw: str) -> Path | None:
        if not raw.strip():
            return None
        path = Path(raw.strip())
        if path.exists():
            path = utils.unique_path(path.parent, path.stem, path.suffix.lstrip("."), set())
        return path

    def _add_files(self, widget: QListWidget, title: str, filters: str) -> None:
        files, _filter = QFileDialog.getOpenFileNames(self, title, "", filters)
        existing = {
            widget.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(widget.count())
        }
        for raw in files:
            if raw in existing:
                continue
            item = QListWidgetItem(Path(raw).name)
            item.setData(Qt.ItemDataRole.UserRole, raw)
            item.setToolTip(raw)
            widget.addItem(item)

    @staticmethod
    def _remove_selected(widget: QListWidget) -> None:
        for item in widget.selectedItems():
            widget.takeItem(widget.row(item))

    @staticmethod
    def _move(widget: QListWidget, offset: int) -> None:
        row = widget.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= widget.count():
            return
        item = widget.takeItem(row)
        widget.insertItem(target, item)
        widget.setCurrentRow(target)

    @staticmethod
    def _paths(widget: QListWidget) -> list[Path]:
        return [
            Path(widget.item(index).data(Qt.ItemDataRole.UserRole))
            for index in range(widget.count())
        ]

    def _warn(self, message: str) -> None:
        QMessageBox.warning(self, tr("pdf_tools"), message)

    def _done(self, message: str) -> None:
        QMessageBox.information(self, tr("pdf_tools"), message)

    # ----------------------------------------------------------------- merge

    def _build_merge_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(QLabel(tr("pdf_files"), tab))
        self.merge_list = QListWidget(tab)
        self.merge_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        list_row = QHBoxLayout()
        list_row.setSpacing(8)
        list_row.addWidget(self.merge_list, 1)
        side = QVBoxLayout()
        side.setSpacing(6)
        side.addWidget(self._ghost(tr("add"), lambda: self._add_files(
            self.merge_list, tr("choose_pdfs"), _PDF_FILTER)))
        side.addWidget(self._ghost(tr("remove"), lambda: self._remove_selected(self.merge_list)))
        side.addWidget(self._ghost(tr("move_up"), lambda: self._move(self.merge_list, -1)))
        side.addWidget(self._ghost(tr("move_down"), lambda: self._move(self.merge_list, 1)))
        side.addStretch(1)
        list_row.addLayout(side)
        layout.addLayout(list_row, 1)

        self.merge_output = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("output_pdf"),
            self.merge_output,
            lambda: self.merge_output.setText(self._pick_save(
                tr("output_pdf"), _PDF_FILTER,
                str(Path.home() / "merged.pdf"))),
        ))
        layout.addLayout(self._action_row(self._primary(tr("pdf_merge"), self._run_merge)))
        return tab

    def _run_merge(self) -> None:
        sources = self._paths(self.merge_list)
        if len(sources) < 2:
            self._warn(tr("merge_need_two"))
            return
        output = self._unique_output(self.merge_output.text())
        if output is None:
            self._warn(tr("no_output"))
            return
        try:
            with _busy():
                pages = pdf_tools.merge_pdfs(sources, output)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("pdf_tool_error"), str(exc))
            return
        self._done(tr("merged_done", n=pages, path=str(output)))

    # ----------------------------------------------------------------- split

    def _build_split_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.split_source = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("source_pdf"), self.split_source, self._pick_split_source))

        self.split_dir = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("output_folder"), self.split_dir, self._pick_split_dir))

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_row.addWidget(QLabel(tr("split_mode"), tab))
        self.split_mode = QComboBox(tab)
        self.split_mode.addItem(tr("split_per_page"), 0)
        self.split_mode.addItem(tr("split_every"), 1)
        self.split_mode.setCurrentIndex(0)
        mode_row.addWidget(self.split_mode)
        mode_row.addSpacing(12)
        mode_row.addWidget(QLabel(tr("pages_per_file"), tab))
        self.split_pages = QSpinBox(tab)
        self.split_pages.setRange(2, 999)
        self.split_pages.setValue(10)
        self.split_pages.setEnabled(False)
        mode_row.addWidget(self.split_pages)
        mode_row.addStretch(1)
        self.split_mode.currentIndexChanged.connect(
            lambda _index: self.split_pages.setEnabled(self.split_mode.currentData() == 1)
        )
        layout.addLayout(mode_row)
        layout.addStretch(1)
        layout.addLayout(self._action_row(self._primary(tr("pdf_split"), self._run_split)))
        return tab

    def _pick_split_source(self) -> None:
        path = self._pick_open(tr("source_pdf"), _PDF_FILTER)
        if path:
            self.split_source.setText(path)
            if not self.split_dir.text().strip():
                self.split_dir.setText(str(Path(path).parent))

    def _pick_split_dir(self) -> None:
        folder = self._pick_dir(tr("output_folder"))
        if folder:
            self.split_dir.setText(folder)

    def _run_split(self) -> None:
        source_text = self.split_source.text().strip()
        if not source_text:
            self._warn(tr("no_input"))
            return
        source = Path(source_text)
        folder_text = self.split_dir.text().strip() or str(source.parent)
        folder = Path(folder_text)
        try:
            folder.mkdir(parents=True, exist_ok=True)
            pages_per_file = 0
            if self.split_mode.currentData() == 1:
                pages_per_file = self.split_pages.value()
            with _busy():
                written = pdf_tools.split_pdf(source, folder, pages_per_file)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("pdf_tool_error"), str(exc))
            return
        self._done(tr("split_done", n=len(written), path=str(folder)))

    # --------------------------------------------------------------- extract

    def _build_extract_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        self.extract_source = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("source_pdf"), self.extract_source, self._pick_extract_source))
        range_row = QHBoxLayout()
        range_row.setSpacing(8)
        range_row.addWidget(QLabel(tr("page_range"), tab))
        self.extract_range = QLineEdit(tab)
        self.extract_range.setPlaceholderText(tr("page_range_hint"))
        range_row.addWidget(self.extract_range, 1)
        layout.addLayout(range_row)
        self.extract_output = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("output_pdf"), self.extract_output, self._pick_extract_output))
        layout.addStretch(1)
        layout.addLayout(self._action_row(self._primary(tr("pdf_extract"), self._run_extract)))
        return tab

    def _pick_extract_source(self) -> None:
        path = self._pick_open(tr("source_pdf"), _PDF_FILTER)
        if path:
            self.extract_source.setText(path)
            if not self.extract_output.text().strip():
                source = Path(path)
                self.extract_output.setText(str(source.with_name(f"{source.stem}_pages.pdf")))

    def _pick_extract_output(self) -> None:
        path = self._pick_save(
            tr("output_pdf"), _PDF_FILTER,
            str(Path.home() / "pages.pdf"),
        )
        if path:
            self.extract_output.setText(path)

    def _run_extract(self) -> None:
        source_text = self.extract_source.text().strip()
        if not source_text:
            self._warn(tr("no_input"))
            return
        output = self._unique_output(self.extract_output.text())
        if output is None:
            self._warn(tr("no_output"))
            return
        try:
            with _busy():
                pages = pdf_tools.extract_pages(
                    Path(source_text), output, self.extract_range.text()
                )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("pdf_tool_error"), str(exc))
            return
        self._done(tr("extracted_done", n=pages, path=str(output)))

    # ----------------------------------------------------------- images->pdf

    def _build_images_pdf_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(QLabel(tr("image_files"), tab))
        self.images_list = QListWidget(tab)
        self.images_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        list_row = QHBoxLayout()
        list_row.setSpacing(8)
        list_row.addWidget(self.images_list, 1)
        side = QVBoxLayout()
        side.setSpacing(6)
        side.addWidget(self._ghost(tr("add"), lambda: self._add_files(
            self.images_list, tr("choose_images"), _IMAGE_FILTER)))
        side.addWidget(self._ghost(tr("remove"), lambda: self._remove_selected(self.images_list)))
        side.addWidget(self._ghost(tr("move_up"), lambda: self._move(self.images_list, -1)))
        side.addWidget(self._ghost(tr("move_down"), lambda: self._move(self.images_list, 1)))
        side.addStretch(1)
        list_row.addLayout(side)
        layout.addLayout(list_row, 1)
        self.images_output = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("output_pdf"), self.images_output,
            lambda: self.images_output.setText(self._pick_save(
                tr("output_pdf"), _PDF_FILTER, str(Path.home() / "images.pdf"))),
        ))
        layout.addLayout(self._action_row(
            self._primary(tr("pdf_images_to_pdf"), self._run_images_pdf)))
        return tab

    def _run_images_pdf(self) -> None:
        sources = self._paths(self.images_list)
        if not sources:
            self._warn(tr("no_input"))
            return
        output = self._unique_output(self.images_output.text())
        if output is None:
            self._warn(tr("no_output"))
            return
        try:
            with _busy():
                pages = pdf_tools.images_to_pdf(sources, output, self.settings.pdf_dpi)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("pdf_tool_error"), str(exc))
            return
        self._done(tr("images_pdf_done", n=pages, path=str(output)))

    # ----------------------------------------------------------- pdf->images

    def _build_pdf_images_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        self.pdf_images_source = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("source_pdf"), self.pdf_images_source, self._pick_pdf_images_source))

        options_row = QHBoxLayout()
        options_row.setSpacing(8)
        options_row.addWidget(QLabel(tr("image_format"), tab))
        self.pdf_images_format = QComboBox(tab)
        self.pdf_images_format.addItem("PNG", "png")
        self.pdf_images_format.addItem("JPG", "jpg")
        options_row.addWidget(self.pdf_images_format)
        options_row.addSpacing(12)
        options_row.addWidget(QLabel(tr("pdf_dpi"), tab))
        self.pdf_images_dpi = QComboBox(tab)
        for dpi in (96, 144, 300):
            self.pdf_images_dpi.addItem(f"{dpi} DPI", dpi)
        index = self.pdf_images_dpi.findData(self.settings.pdf_dpi)
        self.pdf_images_dpi.setCurrentIndex(index if index >= 0 else 1)
        options_row.addWidget(self.pdf_images_dpi)
        options_row.addStretch(1)
        layout.addLayout(options_row)

        range_row = QHBoxLayout()
        range_row.setSpacing(8)
        range_row.addWidget(QLabel(tr("page_range"), tab))
        self.pdf_images_range = QLineEdit(tab)
        self.pdf_images_range.setPlaceholderText(tr("page_range_hint"))
        range_row.addWidget(self.pdf_images_range, 1)
        layout.addLayout(range_row)

        self.pdf_images_output = QLineEdit(tab)
        layout.addLayout(self._file_row(
            tr("output_zip"), self.pdf_images_output, self._pick_pdf_images_output))
        layout.addStretch(1)
        layout.addLayout(self._action_row(
            self._primary(tr("pdf_to_images"), self._run_pdf_images)))
        return tab

    def _pick_pdf_images_source(self) -> None:
        path = self._pick_open(tr("source_pdf"), _PDF_FILTER)
        if path:
            self.pdf_images_source.setText(path)
            if not self.pdf_images_output.text().strip():
                source = Path(path)
                self.pdf_images_output.setText(
                    str(source.with_name(f"{source.stem}_images.zip"))
                )

    def _pick_pdf_images_output(self) -> None:
        path = self._pick_save(
            tr("output_zip"), "ZIP (*.zip)", str(Path.home() / "images.zip")
        )
        if path:
            self.pdf_images_output.setText(path)

    def _run_pdf_images(self) -> None:
        source_text = self.pdf_images_source.text().strip()
        if not source_text:
            self._warn(tr("no_input"))
            return
        output = self._unique_output(self.pdf_images_output.text())
        if output is None:
            self._warn(tr("no_output"))
            return
        try:
            with _busy():
                count = pdf_tools.pdf_to_images(
                    Path(source_text),
                    output,
                    str(self.pdf_images_format.currentData()),
                    int(self.pdf_images_dpi.currentData()),
                    self.pdf_images_range.text(),
                )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("pdf_tool_error"), str(exc))
            return
        self._done(tr("images_zip_done", n=count, path=str(output)))
