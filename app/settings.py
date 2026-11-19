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

    @property
    def pdf_dpi(self) -> int:
        try:
            value = int(self._settings.value("pdf/dpi", 144))
        except (TypeError, ValueError):
            return 144
        if value not in (96, 144, 300):
            return 144
        return value

    @pdf_dpi.setter
    def pdf_dpi(self, value: int) -> None:
        self._settings.setValue("pdf/dpi", int(value))

    @property
    def filename_suffix(self) -> str:
        return str(self._settings.value("output/suffix", ""))

    @filename_suffix.setter
    def filename_suffix(self, value: str) -> None:
        self._settings.setValue("output/suffix", value)

    @property
    def filename_template(self) -> str:
        return str(self._settings.value("output/template", "{name}"))

    @filename_template.setter
    def filename_template(self, value: str) -> None:
        self._settings.setValue("output/template", value)

    @property
    def audio_track(self) -> int:
        try:
            value = int(self._settings.value("media/audio_track", 1))
        except (TypeError, ValueError):
            return 1
        return max(1, min(16, value))

    @audio_track.setter
    def audio_track(self, value: int) -> None:
        self._settings.setValue("media/audio_track", max(1, min(16, int(value))))

    @property
    def subtitle_track(self) -> int:
        try:
            value = int(self._settings.value("media/subtitle_track", 1))
        except (TypeError, ValueError):
            return 1
        return max(1, min(16, value))

    @subtitle_track.setter
    def subtitle_track(self, value: int) -> None:
        self._settings.setValue("media/subtitle_track", max(1, min(16, int(value))))

    @property
    def image_max_size(self) -> int:
        try:
            value = int(self._settings.value("image/max_size", 0))
        except (TypeError, ValueError):
            return 0
        return value if value in (0, 1280, 1920, 2560) else 0

    @image_max_size.setter
    def image_max_size(self, value: int) -> None:
        self._settings.setValue("image/max_size", int(value))

    @property
    def video_height(self) -> int:
        try:
            value = int(self._settings.value("video/height", 0))
        except (TypeError, ValueError):
            return 0
        return value if value in (0, 1080, 720, 480) else 0

    @video_height.setter
    def video_height(self, value: int) -> None:
        self._settings.setValue("video/height", int(value))
