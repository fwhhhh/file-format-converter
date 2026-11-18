"""Main application window."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from PySide6.QtCore import QFileInfo, Qt, QThreadPool
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import i18n
from ..core import detect
from ..core.formats import is_supported_ext
from ..core.jobs import ConvertJob, JobSignals
from ..core.models import Entry
from ..core.utils import resource_path, stem_for, unique_path
from ..engines import engine_for, probe_metadata, status_entries, targets_for
from ..i18n import tr, trn
from ..settings import Settings
from .dialogs import AboutDialog, EngineStatusDialog, OutputDialog, SettingsDialog
from .file_card import FileCard
from .theme import apply_theme
from .widgets import FileDropList


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.entries: dict[int, Entry] = {}
        self.cards: dict[int, FileCard] = {}
        self.items: dict[int, QListWidgetItem] = {}
        self.next_entry_id = 1
        self.running = False
        self.jobs_total = 0
        self.jobs_done = 0
        self.jobs_failed = 0
        self.job_progress: dict[str, float] = {}
        self.job_targets: dict[str, tuple[int, str]] = {}
        self.signals = JobSignals(self)
        self.signals.progress.connect(self._on_job_progress)
        self.signals.done.connect(self._on_job_done)
        self.signals.failed.connect(self._on_job_failed)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(3)
        self.icon_provider = QFileIconProvider()
        self.setAcceptDrops(True)

        self._build_ui()
        self.retranslate()
        self.resize(1120, 760)
        self.setMinimumSize(960, 640)
        self.statusBar().showMessage(tr("ready"))

    # ------------------------------------------------------------- UI setup

    def _build_ui(self) -> None:
        central = QWidget(self)
        central.setObjectName("Root")
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        top_bar = QFrame(central)
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(58)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(18, 8, 14, 8)
        top_layout.setSpacing(4)

        self.brand_icon = QLabel(top_bar)
        self.brand_icon.setFixedSize(24, 24)
        icon = QIcon(str(resource_path("assets/app.ico")))
        pixmap = icon.pixmap(24, 24)
        if not pixmap.isNull():
            self.brand_icon.setPixmap(pixmap)
        self.brand_label = QLabel(top_bar)
        self.brand_label.setObjectName("Brand")
        top_layout.addWidget(self.brand_icon)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.brand_label)
        top_layout.addSpacing(12)

        separator = QFrame(top_bar)
        separator.setObjectName("TopSeparator")
        separator.setFixedSize(1, 20)
        top_layout.addWidget(separator)
        top_layout.addSpacing(8)

        self.action_add_files = QAction(self)
        self.action_add_files.setShortcut(QKeySequence.StandardKey.Open)
        self.action_add_files.triggered.connect(self.choose_files)
        self.action_add_folder = QAction(self)
        self.action_add_folder.triggered.connect(self.choose_folder)
        self.action_clear = QAction(self)
        self.action_clear.triggered.connect(self.clear_entries)
        self.action_settings = QAction(self)
        self.action_settings.setShortcut(QKeySequence("Ctrl+,"))
        self.action_settings.triggered.connect(self.open_settings)
        self.action_about = QAction(self)
        self.action_about.triggered.connect(self.show_about)
        for action in (
            self.action_add_files,
            self.action_add_folder,
            self.action_clear,
            self.action_settings,
            self.action_about,
        ):
            self.addAction(action)

        for action in (self.action_add_files, self.action_add_folder, self.action_clear):
            top_layout.addWidget(self._top_button(action))
        top_layout.addStretch(1)
        for action in (self.action_settings, self.action_about):
            top_layout.addWidget(self._top_button(action))
        root_layout.addWidget(top_bar)

        content = QWidget(central)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 14, 18, 14)
        content_layout.setSpacing(12)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, content)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(12)

        left = QFrame(self.splitter)
        left.setObjectName("Panel")
        left.setMinimumWidth(260)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(10)
        self.files_label = QLabel(left)
        self.files_label.setObjectName("SectionTitle")
        left_layout.addWidget(self.files_label)
        self.file_list = FileDropList(left)
        self.file_list.paths_dropped.connect(self.add_paths)
        self.file_list.remove_requested.connect(self.remove_selected)
        self.file_list.itemSelectionChanged.connect(self._focus_current_card)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_list_menu)
        left_layout.addWidget(self.file_list, 1)
        self.splitter.addWidget(left)

        self.scroll = QScrollArea(self.splitter)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.cards_host = QWidget(self.scroll)
        self.cards_host.setObjectName("CardsHost")
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 8, 0)
        self.cards_layout.setSpacing(12)
        self.empty_label = QLabel(self.cards_host)
        self.empty_label.setObjectName("EmptyHint")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.cards_layout.addWidget(self.empty_label, 1)
        self.cards_layout.addStretch(1)
        self.scroll.setWidget(self.cards_host)
        self.splitter.addWidget(self.scroll)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([320, 780])

        content_layout.addWidget(self.splitter, 1)

        bottom = QFrame(content)
        bottom.setObjectName("BottomBar")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 10, 16, 10)
        bottom_layout.setSpacing(14)
        self.progress = QProgressBar(bottom)
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress_text = QLabel("0/0", bottom)
        self.progress_text.setObjectName("Muted")
        self.progress_text.setMinimumWidth(46)
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_button = QPushButton(bottom)
        self.start_button.setObjectName("Primary")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.setMinimumWidth(124)
        self.start_button.clicked.connect(self.start_conversion)
        bottom_layout.addWidget(self.progress, 1)
        bottom_layout.addWidget(self.progress_text)
        bottom_layout.addWidget(self.start_button)
        content_layout.addWidget(bottom)

        root_layout.addWidget(content, 1)
        self.setCentralWidget(central)

        status_bar = self.statusBar()
        status_bar.setSizeGripEnabled(False)
        self.engine_pill = QPushButton(self)
        self.engine_pill.setObjectName("EnginePill")
        self.engine_pill.setCursor(Qt.CursorShape.PointingHandCursor)
        self.engine_pill.clicked.connect(self.show_engines)
        status_bar.addPermanentWidget(self.engine_pill)

    def _top_button(self, action: QAction) -> QToolButton:
        button = QToolButton(self)
        button.setDefaultAction(action)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setObjectName("Ghost")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return button

    # ------------------------------------------------------------ translation

    def retranslate(self) -> None:
        self.setWindowTitle(tr("app_title"))
        self.brand_label.setText(tr("app_title"))
        self.action_add_files.setText(tr("add_files"))
        self.action_add_folder.setText(tr("add_folder"))
        self.action_clear.setText(tr("clear"))
        self.action_settings.setText(tr("settings"))
        self.action_about.setText(tr("about"))
        self.file_list.set_hint(tr("drop_hint"))
        self.empty_label.setText(tr("empty_right"))
        self._update_controls()
        self._update_engine_label()
        for card in self.cards.values():
            card.retranslate()
        self._update_apply_buttons()

    def _update_engine_label(self) -> None:
        entries = status_entries()
        available = sum(1 for _key, _label, ok in entries if ok)
        self.engine_pill.setText(tr("engine_pill", ok=available, total=len(entries)))
        self.engine_pill.setToolTip(tr("engine_status_tip"))

    # ------------------------------------------------------------- file input

    def choose_files(self) -> None:
        files, _filter = QFileDialog.getOpenFileNames(self, tr("add_files"))
        if files:
            self.add_paths(files)

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("add_folder"))
        if folder:
            self.add_paths([folder])

    def add_paths(self, raw_paths: list[str]) -> None:
        if self.running or not raw_paths:
            return
        files: list[Path] = []
        for raw in raw_paths:
            path = Path(raw)
            if path.is_dir():
                try:
                    files.extend(sorted(item for item in path.rglob("*") if item.is_file()))
                except OSError:
                    continue
            elif path.is_file():
                files.append(path)
        if not files:
            return

        seen = {str(entry.path.resolve()).lower() for entry in self.entries.values()}
        added = 0
        duplicates = 0
        skipped_files: list[Path] = []
        last_card: FileCard | None = None
        for file in files:
            try:
                ext = detect.sniff_ext(file)
                size = file.stat().st_size
            except OSError:
                skipped_files.append(file)
                continue
            if ext is None or not is_supported_ext(ext):
                skipped_files.append(file)
                continue
            targets = targets_for(ext)
            if not targets:
                skipped_files.append(file)
                continue
            key = str(file.resolve()).lower()
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            meta = probe_metadata(ext, file)
            entry = Entry(self.next_entry_id, file, ext, size, targets, meta)
            self.next_entry_id += 1
            self.entries[entry.entry_id] = entry
            last_card = self._add_card(entry)
            added += 1

        if last_card is not None:
            self.scroll.ensureWidgetVisible(last_card)
        if added == 0 and skipped_files:
            names = "\n".join(path.name for path in skipped_files[:10])
            QMessageBox.warning(
                self,
                tr("unsupported_title"),
                tr("unsupported_body", names=names),
            )
        else:
            parts = []
            if added:
                parts.append(trn("added_one", "added_many", added))
            if skipped_files:
                parts.append(trn("skipped_one", "skipped_many", len(skipped_files)))
            if duplicates:
                parts.append(trn("duplicate_skipped_one", "duplicate_skipped_many", duplicates))
            if parts:
                self.statusBar().showMessage("  ".join(parts), 10000)
        self._update_controls()
        self._update_apply_buttons()

    def _add_card(self, entry: Entry) -> FileCard:
        card = FileCard(entry, self.cards_host)
        card.selection_changed.connect(self._update_controls)
        card.apply_requested.connect(self._apply_to_same_type)
        self.cards[entry.entry_id] = card
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        item = QListWidgetItem(
            self.icon_provider.icon(QFileInfo(str(entry.path))),
            entry.path.name,
        )
        item.setData(Qt.ItemDataRole.UserRole, entry.entry_id)
        item.setToolTip(str(entry.path))
        self.file_list.addItem(item)
        self.items[entry.entry_id] = item
        self.empty_label.setVisible(False)
        self.file_list.setCurrentItem(item)
        self.file_list.clearSelection()
        item.setSelected(True)
        return card

    def _remove_entry(self, entry_id: int) -> None:
        if entry_id not in self.entries:
            return
        self.entries.pop(entry_id, None)
        card = self.cards.pop(entry_id, None)
        if card is not None:
            self.cards_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        item = self.items.pop(entry_id, None)
        if item is not None:
            row = self.file_list.row(item)
            if row >= 0:
                self.file_list.takeItem(row)
        self._after_entries_changed()

    def remove_selected(self) -> None:
        if self.running:
            return
        selected = self.file_list.selectedItems()
        if not selected:
            return
        entry_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected]
        for entry_id in entry_ids:
            self._remove_entry(entry_id)

    def clear_entries(self) -> None:
        if self.running:
            return
        for entry_id in list(self.entries.keys()):
            self._remove_entry(entry_id)

    def _after_entries_changed(self) -> None:
        self.empty_label.setVisible(not self.entries)
        if not self.entries:
            self.progress.setValue(0)
            self.progress_text.setText("0/0")
        self._update_controls()
        self._update_apply_buttons()

    # ------------------------------------------------------------- settings UI

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        i18n.set_language(self.settings.language)
        apply_theme(QApplication.instance(), self.settings.theme)
        self.retranslate()

    def show_about(self) -> None:
        AboutDialog(self).exec()

    def show_engines(self, _checked: bool = False) -> None:
        EngineStatusDialog(self).exec()

    # ------------------------------------------------------------ conversion

    def start_conversion(self) -> None:
        if self.running:
            return
        if not self.entries:
            QMessageBox.information(self, tr("no_files_title"), tr("no_files_body"))
            return
        selections = {
            entry_id: card.selected_formats() for entry_id, card in self.cards.items()
        }
        if not any(selections.values()):
            QMessageBox.information(self, tr("no_selection_title"), tr("no_selection_body"))
            return

        dialog = OutputDialog(self.settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        custom_folder = dialog.custom_folder()

        reserved: set[str] = set()
        jobs: list[ConvertJob] = []
        self.job_targets.clear()
        options = {"quality": self.settings.quality, "preset": self.settings.preset}
        for entry in self.entries.values():
            card = self.cards.get(entry.entry_id)
            if card is None:
                continue
            chosen = card.selected_formats()
            ordered = [fmt for fmt in entry.targets if fmt in chosen]
            if not ordered:
                continue
            folder = custom_folder if custom_folder is not None else entry.path.parent
            stem = stem_for(entry.path, entry.ext)
            destinations: dict[str, Path] = {}
            for fmt in ordered:
                destinations[fmt] = unique_path(folder, stem, fmt, reserved)
            card.prepare_results(destinations)
            for fmt in ordered:
                engine = engine_for(entry.ext, fmt)
                if engine is None:
                    card.set_failed(fmt, tr("error_missing_engine"))
                    continue
                job_id = f"{entry.entry_id}:{fmt}"
                self.job_targets[job_id] = (entry.entry_id, fmt)
                jobs.append(
                    ConvertJob(
                        job_id,
                        engine,
                        entry.path,
                        destinations[fmt],
                        options,
                        self.signals,
                    )
                )
                card.set_running(fmt)

        if not jobs:
            return
        self.running = True
        self.jobs_total = len(jobs)
        self.jobs_done = 0
        self.jobs_failed = 0
        self.job_progress.clear()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress_text.setText(f"0/{self.jobs_total}")
        self.statusBar().showMessage(tr("preparing"))
        self._update_controls()
        for job in jobs:
            self.pool.start(job)

    def _on_job_progress(self, job_id: str, fraction: float) -> None:
        self.job_progress[job_id] = max(0.0, min(1.0, float(fraction)))
        self._refresh_progress()

    def _on_job_done(self, job_id: str, out_path: str) -> None:
        self.job_progress.pop(job_id, None)
        target = self.job_targets.pop(job_id, None)
        if target is not None:
            entry_id, fmt = target
            self.jobs_done += 1
            card = self.cards.get(entry_id)
            if card is not None:
                card.set_result(fmt, Path(out_path))
        self._refresh_progress()
        self._finish_if_done()

    def _on_job_failed(self, job_id: str, message: str) -> None:
        self.job_progress.pop(job_id, None)
        target = self.job_targets.pop(job_id, None)
        if target is not None:
            entry_id, fmt = target
            self.jobs_done += 1
            self.jobs_failed += 1
            card = self.cards.get(entry_id)
            if card is not None:
                card.set_failed(fmt, message)
        self._refresh_progress()
        self._finish_if_done()

    def _refresh_progress(self) -> None:
        if self.jobs_total <= 0:
            return
        fraction = (self.jobs_done + sum(self.job_progress.values())) / self.jobs_total
        fraction = max(0.0, min(1.0, fraction))
        self.progress.setValue(int(fraction * 1000))
        self.progress_text.setText(f"{self.jobs_done}/{self.jobs_total}")

    def _finish_if_done(self) -> None:
        if not self.running or self.jobs_done < self.jobs_total:
            return
        self.running = False
        self._update_controls()
        self.progress.setValue(1000)
        self.progress_text.setText(f"{self.jobs_total}/{self.jobs_total}")
        succeeded = self.jobs_total - self.jobs_failed
        self.statusBar().showMessage(
            tr("summary", ok=succeeded, fail=self.jobs_failed), 12000
        )

    # -------------------------------------------------------------- controls

    def _update_controls(self) -> None:
        has_entries = bool(self.entries)
        has_selection = any(card.selected_formats() for card in self.cards.values())
        self.files_label.setText(
            tr("files_title", n=len(self.entries)) if has_entries else tr("files_empty")
        )
        self.empty_label.setVisible(not has_entries)
        self.action_add_files.setEnabled(not self.running)
        self.action_add_folder.setEnabled(not self.running)
        self.action_clear.setEnabled(not self.running and has_entries)
        self.file_list.setEnabled(not self.running)
        self.start_button.setText(tr("converting") if self.running else tr("start"))
        self.start_button.setEnabled(not self.running and has_entries and has_selection)

    def _update_apply_buttons(self) -> None:
        counts = Counter(entry.ext for entry in self.entries.values())
        for entry in self.entries.values():
            card = self.cards.get(entry.entry_id)
            if card is not None:
                card.set_apply_visible(counts[entry.ext] > 1)

    def _apply_to_same_type(self, entry_id: int, formats_set: set) -> None:
        entry = self.entries.get(entry_id)
        if entry is None:
            return
        for other in self.entries.values():
            if other.entry_id == entry_id or other.ext != entry.ext:
                continue
            card = self.cards.get(other.entry_id)
            if card is not None:
                card.set_selected_formats(formats_set)

    def _focus_current_card(self) -> None:
        selected = self.file_list.selectedItems()
        if not selected:
            return
        entry_id = selected[-1].data(Qt.ItemDataRole.UserRole)
        card = self.cards.get(entry_id)
        if card is not None:
            self.scroll.ensureWidgetVisible(card)

    def _show_list_menu(self, pos) -> None:
        menu = QMenu(self)
        action = menu.addAction(tr("remove"))
        action.setEnabled(not self.running)
        chosen = menu.exec(self.file_list.viewport().mapToGlobal(pos))
        if chosen == action:
            self.remove_selected()

    # ---------------------------------------------------------- window drops

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.running:
            answer = QMessageBox.question(
                self,
                tr("quit_title"),
                tr("quit_body"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.signals.blockSignals(True)
            self.pool.waitForDone()
        event.accept()

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if paths:
            self.add_paths(paths)
            event.acceptProposedAction()
            return
        event.ignore()
