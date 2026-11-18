"""Theme application: fonts, palette and the global style sheet."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

from ..core.utils import resource_path
from . import style
from .style import ThemeColors

_FONT_FAMILIES = [
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "Segoe UI",
    "Noto Sans CJK SC",
    "Arial",
]


def system_is_dark(app: QApplication) -> bool:
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except (AttributeError, TypeError):
        return False


def _palette(colors: ThemeColors) -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors.bg))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.surface_alt))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(colors.danger))
    palette.setColor(QPalette.ColorRole.Link, QColor(colors.accent))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.accent))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.accent_text))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors.text_muted))
    palette.setColor(QPalette.ColorRole.Light, QColor(colors.surface_hover))
    palette.setColor(QPalette.ColorRole.Midlight, QColor(colors.surface_alt))
    palette.setColor(QPalette.ColorRole.Mid, QColor(colors.border))
    palette.setColor(QPalette.ColorRole.Dark, QColor(colors.bg))
    palette.setColor(QPalette.ColorRole.Shadow, QColor(0, 0, 0))
    if hasattr(QPalette.ColorRole, "Accent"):
        palette.setColor(QPalette.ColorRole.Accent, QColor(colors.accent))
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(colors.text_muted))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Base,
        QColor(colors.surface_alt),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Button,
        QColor(colors.surface_alt),
    )
    return palette


def apply_theme(app: QApplication, mode: str) -> None:
    """Apply one of: system, light, dark.

    A fixed palette and style sheet are used so the result looks the same on
    every machine instead of inheriting Windows accent colours.
    """
    app.setStyle("Fusion")
    use_dark = mode == "dark" or (mode == "system" and system_is_dark(app))
    colors = style.DARK if use_dark else style.LIGHT
    style.set_current(colors)

    font = QFont()
    font.setFamilies(_FONT_FAMILIES)
    font.setFamily(_FONT_FAMILIES[0])
    font.setPointSize(10)
    app.setFont(font)

    app.setPalette(_palette(colors))
    arrow = resource_path("assets/chevron-down.svg").as_posix()
    app.setStyleSheet(style.build_stylesheet(colors, arrow))
