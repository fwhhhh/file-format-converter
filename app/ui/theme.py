"""Theme helpers (light / dark, optionally following the system)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

_ACCENT = QColor(47, 111, 208)
_ACCENT_TEXT = QColor(255, 255, 255)


def _light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(246, 246, 246))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.Text, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(200, 30, 30))
    palette.setColor(QPalette.ColorRole.Link, _ACCENT)
    palette.setColor(QPalette.ColorRole.Highlight, _ACCENT)
    palette.setColor(QPalette.ColorRole.HighlightedText, _ACCENT_TEXT)
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(135, 135, 135))
    if hasattr(QPalette.ColorRole, "Accent"):
        palette.setColor(QPalette.ColorRole.Accent, _ACCENT)
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(150, 150, 150))
    return palette


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(228, 228, 228))
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(228, 228, 228))
    palette.setColor(QPalette.ColorRole.Text, QColor(228, 228, 228))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(228, 228, 228))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 90, 90))
    palette.setColor(QPalette.ColorRole.Link, QColor(110, 170, 245))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(150, 150, 150))
    palette.setColor(QPalette.ColorRole.Light, QColor(90, 90, 90))
    palette.setColor(QPalette.ColorRole.Midlight, QColor(70, 70, 70))
    palette.setColor(QPalette.ColorRole.Mid, QColor(60, 60, 60))
    palette.setColor(QPalette.ColorRole.Dark, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.Shadow, QColor(0, 0, 0))
    if hasattr(QPalette.ColorRole, "Accent"):
        palette.setColor(QPalette.ColorRole.Accent, QColor(42, 130, 218))
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(120, 120, 120))
    return palette


def system_is_dark(app: QApplication) -> bool:
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except (AttributeError, TypeError):
        return False


def apply_theme(app: QApplication, mode: str) -> None:
    """Apply one of: system, light, dark. Uses fixed palettes so the look is
    identical on every machine (Windows accent colours are not inherited)."""
    app.setStyle("Fusion")
    use_dark = mode == "dark" or (mode == "system" and system_is_dark(app))
    app.setPalette(_dark_palette() if use_dark else _light_palette())
