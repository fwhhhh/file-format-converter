"""Conversion jobs executed on a QThreadPool."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal

from ..engines.base import Engine


class JobSignals(QObject):
    progress = Signal(str, float)
    done = Signal(str, str)
    failed = Signal(str, str)


class ConvertJob(QRunnable):
    def __init__(
        self,
        job_id: str,
        engine: Engine,
        src: Path,
        dst: Path,
        options: dict,
        signals: JobSignals,
    ) -> None:
        super().__init__()
        self.job_id = job_id
        self.engine = engine
        self.src = src
        self.dst = dst
        self.options = options
        self.signals = signals

    def run(self) -> None:
        try:
            self.engine.convert(self.src, self.dst, self.options, self._report)
        except Exception as exc:  # noqa: BLE001 - reported to the UI
            try:
                if self.dst.exists():
                    self.dst.unlink()
            except OSError:
                pass
            message = str(exc).strip() or self.__class__.__name__
            self.signals.failed.emit(self.job_id, message)
            return
        self.signals.done.emit(self.job_id, str(self.dst))

    def _report(self, fraction: float) -> None:
        self.signals.progress.emit(self.job_id, float(fraction))
