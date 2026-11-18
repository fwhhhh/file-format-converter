"""Word / Excel / PowerPoint conversions through the installed Office suite.

The app never bundles Office; it only automates an existing installation via
COM.  When Office is missing the corresponding targets simply disappear.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from .base import Engine, EngineError, Progress

WORD_SOURCES = {"docx", "doc", "odt", "rtf"}
EXCEL_SOURCES = {"xlsx", "xls"}
POWERPOINT_SOURCES = {"pptx", "ppt"}

_APP_EXES = {
    "word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE",
}
_APP_PROG_IDS = {
    "word": "Word.Application",
    "excel": "Excel.Application",
    "powerpoint": "PowerPoint.Application",
}

_WD_FORMAT_DOCX = 16
_WD_EXPORT_PDF = 17
_XL_TYPE_PDF = 0
_XL_FORMAT_XLSX = 51
_PP_SAVE_PDF = 32

_CACHE: dict[str, str | None] = {}


def _registry_app_path(exe: str) -> str | None:
    if sys.platform != "win32":
        return None
    try:
        import winreg
    except ImportError:
        return None
    keys = [
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"),
        (winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"),
    ]
    views = [winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY]
    for root, path in keys:
        for view in views:
            try:
                with winreg.OpenKey(root, path, 0, winreg.KEY_READ | view) as key:
                    value, _kind = winreg.QueryValueEx(key, "")
            except OSError:
                continue
            if value and Path(value).exists():
                return str(value)
    return None


def find_office_exe(app: str) -> str | None:
    if app in _CACHE:
        return _CACHE[app]
    exe = _APP_EXES.get(app)
    found: str | None = None
    if exe:
        found = _registry_app_path(exe)
        if found is None:
            roots = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")]
            for root in roots:
                if not root:
                    continue
                for version in ("Office16", "Office15", "Office14"):
                    candidates = [
                        Path(root) / "Microsoft Office" / "Root" / version / exe,
                        Path(root) / "Microsoft Office" / version / exe,
                    ]
                    for candidate in candidates:
                        if candidate.exists():
                            found = str(candidate)
                            break
                    if found:
                        break
                if found:
                    break
    _CACHE[app] = found
    return found


def office_apps() -> dict[str, bool]:
    return {app: find_office_exe(app) is not None for app in _APP_EXES}


def _com_message(exc: Exception) -> str:
    try:
        info = getattr(exc, "excepinfo", None)
        if info and len(info) > 2 and info[2]:
            return str(info[2])
    except Exception:
        pass
    text = str(exc).strip()
    return text[-800:] if len(text) > 800 else text


@contextmanager
def _office_instance(prog_id: str, quit_on_exit: bool = True):
    try:
        import pythoncom
        import win32com.client
    except Exception as exc:  # noqa: BLE001
        raise EngineError("pywin32 is required for Office conversion") from exc

    pythoncom.CoInitialize()
    application = None
    try:
        application = win32com.client.DispatchEx(prog_id)
        yield application
    except EngineError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise EngineError(_com_message(exc)) from exc
    finally:
        if application is not None and quit_on_exit:
            try:
                application.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def _word_convert(src: Path, dst: Path, target: str) -> None:
    with _office_instance(_APP_PROG_IDS["word"]) as word:
        try:
            word.Visible = False
        except Exception:
            pass
        try:
            word.DisplayAlerts = 0
            word.AutomationSecurity = 3
            word.Options.ConfirmConversions = False
        except Exception:
            pass
        document = None
        try:
            document = word.Documents.Open(
                str(src),
                ConfirmConversions=False,
                ReadOnly=(target == "pdf"),
                AddToRecentFiles=False,
                PasswordDocument="",
                WritePasswordDocument="",
            )
            if target == "pdf":
                document.ExportAsFixedFormat(str(dst), _WD_EXPORT_PDF)
            else:
                document.SaveAs2(str(dst), FileFormat=_WD_FORMAT_DOCX)
        finally:
            if document is not None:
                try:
                    document.Close(SaveChanges=0)
                except Exception:
                    pass


def _excel_convert(src: Path, dst: Path, target: str) -> None:
    with _office_instance(_APP_PROG_IDS["excel"]) as excel:
        try:
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.EnableEvents = False
            excel.AskToUpdateLinks = False
        except Exception:
            pass
        workbook = None
        try:
            workbook = excel.Workbooks.Open(
                str(src),
                UpdateLinks=0,
                ReadOnly=(target == "pdf"),
                AddToMru=False,
            )
            if target == "pdf":
                workbook.ExportAsFixedFormat(_XL_TYPE_PDF, str(dst))
            else:
                workbook.SaveAs(str(dst), FileFormat=_XL_FORMAT_XLSX)
        finally:
            if workbook is not None:
                try:
                    workbook.Close(SaveChanges=False)
                except Exception:
                    pass


def _powerpoint_convert(src: Path, dst: Path) -> None:
    with _office_instance(_APP_PROG_IDS["powerpoint"], quit_on_exit=False) as powerpoint:
        try:
            powerpoint.DisplayAlerts = 1
        except Exception:
            pass
        try:
            had_presentations = powerpoint.Presentations.Count > 0
        except Exception:
            had_presentations = True
        presentation = None
        try:
            presentation = powerpoint.Presentations.Open(
                str(src),
                ReadOnly=True,
                Untitled=False,
                WithWindow=False,
            )
            presentation.SaveAs(str(dst), _PP_SAVE_PDF)
        finally:
            if presentation is not None:
                try:
                    presentation.Close()
                except Exception:
                    pass
            if not had_presentations:
                try:
                    powerpoint.Quit()
                except Exception:
                    pass


class OfficeEngine(Engine):
    key = "office"
    label_key = "engine_office"

    def available(self) -> bool:
        return any(find_office_exe(app) for app in _APP_EXES)

    def targets(self, src_ext: str) -> list[str]:
        result: list[str] = []
        word_ready = find_office_exe("word") is not None
        excel_ready = find_office_exe("excel") is not None
        powerpoint_ready = find_office_exe("powerpoint") is not None
        if word_ready:
            if src_ext in WORD_SOURCES:
                result.append("pdf")
            if src_ext == "pdf":
                result.append("docx")
        if excel_ready and src_ext in EXCEL_SOURCES:
            result.append("pdf")
            if src_ext == "xls":
                result.append("xlsx")
        if powerpoint_ready and src_ext in POWERPOINT_SOURCES:
            result.append("pdf")
        return result

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        source_ext = str(
            options.get("source_format") or src.suffix.lower().lstrip(".")
        )
        target = str(options.get("target_format") or dst.suffix.lower().lstrip("."))
        if progress is not None:
            progress(0.05)
        try:
            if target == "pdf" and source_ext in WORD_SOURCES:
                _word_convert(src, dst, "pdf")
            elif target == "docx" and source_ext == "pdf":
                _word_convert(src, dst, "docx")
            elif target == "pdf" and source_ext in EXCEL_SOURCES:
                _excel_convert(src, dst, "pdf")
            elif target == "xlsx" and source_ext == "xls":
                _excel_convert(src, dst, "xlsx")
            elif target == "pdf" and source_ext in POWERPOINT_SOURCES:
                _powerpoint_convert(src, dst)
            else:
                raise EngineError(
                    f"Unsupported Office conversion: {source_ext} -> {target}"
                )
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(_com_message(exc)) from exc
        if progress is not None:
            progress(1.0)
