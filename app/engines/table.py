"""CSV and XLSX conversions backed by openpyxl."""

from __future__ import annotations

import csv
from pathlib import Path

from .base import Engine, EngineError, Progress
from .text import _decode

TABLE_EXTS = {"csv", "xlsx"}


class TableEngine(Engine):
    key = "table"
    label_key = "engine_table"

    def available(self) -> bool:
        try:
            import openpyxl  # noqa: F401
        except Exception:
            return False
        return True

    def targets(self, src_ext: str) -> list[str]:
        if src_ext not in TABLE_EXTS:
            return []
        return [fmt for fmt in ("xlsx", "csv") if fmt != src_ext]

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        from openpyxl import Workbook, load_workbook

        source_ext = src.suffix.lower().lstrip(".")
        target = dst.suffix.lower().lstrip(".")
        try:
            if source_ext == "csv" and target == "xlsx":
                text = _decode(src.read_bytes())
                workbook = Workbook()
                sheet = workbook.active
                for row in csv.reader(text.splitlines()):
                    sheet.append(row)
                workbook.save(dst)
            elif source_ext == "xlsx" and target == "csv":
                workbook = load_workbook(src, read_only=True, data_only=True)
                sheet = workbook.active
                with open(dst, "w", encoding="utf-8-sig", newline="") as handle:
                    writer = csv.writer(handle)
                    for row in sheet.iter_rows(values_only=True):
                        writer.writerow(["" if value is None else value for value in row])
                workbook.close()
            else:
                raise EngineError(f"Unsupported table conversion: {source_ext} -> {target}")
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        if progress is not None:
            progress(1.0)
