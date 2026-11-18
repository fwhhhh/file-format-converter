"""Conversion jobs executed on a QThreadPool."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal

from ..engines.base import CancelledError, Engine


class JobSignals(QObject):
    progress = Signal(str, float)
    done = Signal(str, str)
    failed = Signal(str, str)
    cancelled = Signal(str)


class ConvertJob(QRunnable):
    def __init__(
        self,
        job_id: str,
        engine: Engine,
        src: Path,
        dst: Path,
        options: dict,
        signals: JobSignals,
        cancel_event: threading.Event | None = None,
    ) -> None:
        super().__init__()
        self.job_id = job_id
        self.engine = engine
        self.src = src
        self.dst = dst
        self.options = options
        self.signals = signals
        self.cancel_event = cancel_event
        self._cancelled = False

    def _is_cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    def run(self) -> None:
        if self._is_cancelled():
            self.signals.cancelled.emit(self.job_id)
            return
        options = dict(self.options)
        if self.cancel_event is not None:
            options["cancel_event"] = self.cancel_event
        try:
            self.engine.convert(self.src, self.dst, options, self._report)
        except CancelledError:
            self._cleanup()
            self.signals.cancelled.emit(self.job_id)
            return
        except Exception as exc:  # noqa: BLE001 - reported to the UI
            self._cleanup()
            message = str(exc).strip() or self.__class__.__name__
            self.signals.failed.emit(self.job_id, message)
            return
        if self._is_cancelled():
            self._cleanup()
            self.signals.cancelled.emit(self.job_id)
            return
        self.signals.done.emit(self.job_id, str(self.dst))

    def _cleanup(self) -> None:
        try:
            if self.dst.exists():
                self.dst.unlink()
        except OSError:
            pass

    def _report(self, fraction: float) -> None:
        if self._is_cancelled():
            return
        self.signals.progress.emit(self.job_id, float(fraction))
