"""Persistent application settings stored with QSettings."""

from __future__ import annotations

from PySide6.QtCore import QLocale, QSettings


def _system_language() -> str:
    if QLocale.system().language() == QLocale.Language.Chinese:
        return "zh"
    return "en"


class Settings:
    def __init__(self) -> None:
        self._settings = QSettings("FileFormatConverter", "FileFormatConverter")

    @property
    def language(self) -> str:
        value = str(self._settings.value("ui/language", _system_language()))
        if value not in ("zh", "en"):
            return _system_language()
        return value

    @language.setter
    def language(self, value: str) -> None:
        self._settings.setValue("ui/language", value)

    @property
    def theme(self) -> str:
        value = str(self._settings.value("ui/theme", "system"))
        if value not in ("system", "light", "dark"):
            return "system"
        return value

    @theme.setter
    def theme(self, value: str) -> None:
        self._settings.setValue("ui/theme", value)

    @property
    def quality(self) -> int:
        try:
            value = int(self._settings.value("image/quality", 85))
        except (TypeError, ValueError):
            return 85
        return max(1, min(100, value))

    @quality.setter
    def quality(self, value: int) -> None:
        self._settings.setValue("image/quality", max(1, min(100, int(value))))

    @property
    def preset(self) -> str:
        value = str(self._settings.value("video/preset", "balanced"))
        if value not in ("high", "balanced", "small"):
            return "balanced"
        return value

    @preset.setter
    def preset(self, value: str) -> None:
        self._settings.setValue("video/preset", value)

    @property
    def custom_output_dir(self) -> str:
        return str(self._settings.value("output/custom_dir", ""))

    @custom_output_dir.setter
    def custom_output_dir(self, value: str) -> None:
        self._settings.setValue("output/custom_dir", value)
