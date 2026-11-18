"""Visual design tokens and the global Qt style sheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeColors:
    bg: str
    surface: str
    surface_alt: str
    surface_hover: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_soft: str
    accent_text: str
    success: str
    danger: str
    chip_bg: str
    chip_border: str
    chip_text: str
    progress_track: str
    selection_bg: str
    selection_text: str


LIGHT = ThemeColors(
    bg="#f5f6f8",
    surface="#ffffff",
    surface_alt="#f3f5f8",
    surface_hover="#eef2f7",
    border="#e3e7ee",
    text="#1f2937",
    text_muted="#6b7280",
    accent="#2563eb",
    accent_hover="#1d4ed8",
    accent_soft="#e8f0fe",
    accent_text="#ffffff",
    success="#16a34a",
    danger="#dc2626",
    chip_bg="#f3f4f6",
    chip_border="#e5e7eb",
    chip_text="#374151",
    progress_track="#e8edf5",
    selection_bg="#e8f0fe",
    selection_text="#1e3a8a",
)

DARK = ThemeColors(
    bg="#141518",
    surface="#1e1f23",
    surface_alt="#26272c",
    surface_hover="#2c2e34",
    border="#2e3036",
    text="#e5e7eb",
    text_muted="#9ca3af",
    accent="#3b82f6",
    accent_hover="#60a5fa",
    accent_soft="#1e3a5f",
    accent_text="#ffffff",
    success="#4ade80",
    danger="#f87171",
    chip_bg="#27292f",
    chip_border="#3a3d45",
    chip_text="#d1d5db",
    progress_track="#2a2c32",
    selection_bg="#1f3355",
    selection_text="#dbeafe",
)

_CURRENT = LIGHT


def set_current(colors: ThemeColors) -> None:
    global _CURRENT
    _CURRENT = colors


def current_colors() -> ThemeColors:
    return _CURRENT


def build_stylesheet(c: ThemeColors, down_arrow: str = "") -> str:
    arrow_rule = ""
    if down_arrow:
        arrow_rule = f'''
    QComboBox::down-arrow {{
        image: url("{down_arrow}");
        width: 12px;
        height: 12px;
    }}'''
    return f"""
    QWidget {{
        color: {c.text};
    }}
    QWidget#Root {{
        background-color: {c.bg};
    }}
    QWidget#CardsHost {{
        background-color: transparent;
    }}
    QLabel {{
        background-color: transparent;
    }}
    QLabel#Brand {{
        font-size: 16px;
        font-weight: 700;
        color: {c.text};
    }}
    QLabel#SectionTitle {{
        font-size: 13px;
        font-weight: 600;
        color: {c.text};
    }}
    QLabel#CardTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {c.text};
    }}
    QLabel#Muted {{
        font-size: 12px;
        color: {c.text_muted};
    }}
    QLabel#EmptyHint {{
        font-size: 14px;
        color: {c.text_muted};
    }}
    QLabel#AboutTitle {{
        font-size: 20px;
        font-weight: 700;
        color: {c.text};
    }}
    QLabel#AuthorPill {{
        background-color: {c.accent_soft};
        color: {c.accent};
        border-radius: 11px;
        padding: 5px 14px;
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel[kind="ok"] {{
        color: {c.success};
        font-weight: 700;
    }}
    QLabel[kind="fail"] {{
        color: {c.danger};
        font-weight: 700;
    }}
    QLabel[kind="idle"] {{
        color: {c.text_muted};
    }}
    QLabel[kind="missing"] {{
        color: {c.text_muted};
    }}

    QFrame#TopBar {{
        background-color: {c.surface};
        border: none;
        border-bottom: 1px solid {c.border};
    }}
    QFrame#TopSeparator {{
        background-color: {c.border};
        border: none;
    }}
    QFrame#Panel {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 14px;
    }}
    QFrame#Card {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 14px;
    }}
    QFrame#ResultRow {{
        background-color: {c.surface_alt};
        border: none;
        border-radius: 8px;
    }}
    QFrame#BottomBar {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 12px;
    }}

    QToolButton#Ghost, QPushButton#Ghost {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        padding: 6px 11px;
        color: {c.chip_text};
        font-size: 13px;
    }}
    QToolButton#Ghost:hover, QPushButton#Ghost:hover {{
        background-color: {c.surface_hover};
        color: {c.text};
    }}
    QToolButton#Ghost:pressed, QPushButton#Ghost:pressed {{
        background-color: {c.surface_alt};
    }}
    QToolButton#Ghost:disabled, QPushButton#Ghost:disabled {{
        color: {c.text_muted};
        background-color: transparent;
    }}
    QPushButton#LinkGhost {{
        background-color: transparent;
        border: none;
        border-radius: 6px;
        padding: 4px 8px;
        color: {c.accent};
        font-size: 12px;
    }}
    QPushButton#LinkGhost:hover {{
        background-color: {c.accent_soft};
    }}
    QPushButton#LinkGhost:disabled {{
        color: {c.text_muted};
        background-color: transparent;
    }}
    QToolButton#CardToggle {{
        background-color: transparent;
        border: none;
        color: {c.text_muted};
        font-size: 12px;
        padding: 0px;
    }}
    QPushButton#Chip {{
        background-color: {c.chip_bg};
        border: 1px solid {c.chip_border};
        border-radius: 13px;
        padding: 6px 14px;
        color: {c.chip_text};
        font-size: 13px;
        min-height: 18px;
    }}
    QPushButton#Chip:hover {{
        border-color: {c.accent};
        color: {c.accent};
    }}
    QPushButton#Chip:checked {{
        background-color: {c.accent};
        border-color: {c.accent};
        color: {c.accent_text};
        font-weight: 600;
    }}
    QPushButton#Chip:checked:hover {{
        background-color: {c.accent_hover};
        border-color: {c.accent_hover};
    }}
    QPushButton#Primary {{
        background-color: {c.accent};
        border: none;
        border-radius: 10px;
        padding: 9px 26px;
        color: {c.accent_text};
        font-size: 14px;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{
        background-color: {c.accent_hover};
    }}
    QPushButton#Primary:pressed {{
        background-color: {c.accent};
    }}
    QPushButton#Primary:disabled {{
        background-color: {c.chip_bg};
        color: {c.text_muted};
    }}
    QPushButton#EnginePill {{
        background-color: {c.accent_soft};
        border: none;
        border-radius: 10px;
        padding: 4px 12px;
        color: {c.accent};
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#EnginePill:hover {{
        background-color: {c.selection_bg};
    }}

    QPushButton {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 7px 16px;
        color: {c.text};
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {c.surface_hover};
    }}
    QPushButton:pressed {{
        background-color: {c.surface_alt};
    }}
    QPushButton:disabled {{
        color: {c.text_muted};
        background-color: {c.surface_alt};
        border-color: {c.border};
    }}
    QPushButton:default {{
        background-color: {c.accent};
        border-color: {c.accent};
        color: {c.accent_text};
        font-weight: 600;
    }}
    QPushButton:default:hover {{
        background-color: {c.accent_hover};
        border-color: {c.accent_hover};
    }}

    QLineEdit, QComboBox {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 7px 10px;
        color: {c.text};
        font-size: 13px;
        min-height: 18px;
        selection-background-color: {c.accent};
        selection-color: {c.accent_text};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border-color: {c.accent};
    }}
    QLineEdit:disabled {{
        color: {c.text_muted};
        background-color: {c.surface_alt};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}{arrow_rule}
    QComboBox QAbstractItemView {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 4px;
        outline: none;
        selection-background-color: {c.selection_bg};
        selection-color: {c.text};
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 24px;
        padding: 3px 8px;
    }}
    QSlider::groove:horizontal {{
        height: 4px;
        background-color: {c.progress_track};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background-color: {c.accent};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
        background-color: {c.accent};
    }}
    QSlider::handle:horizontal:hover {{
        background-color: {c.accent_hover};
    }}
    QRadioButton {{
        spacing: 8px;
        font-size: 13px;
    }}
    QSpinBox {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 6px 8px;
        color: {c.text};
        font-size: 13px;
        min-height: 18px;
    }}
    QSpinBox:focus {{
        border-color: {c.accent};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 16px;
        border: none;
        background-color: transparent;
    }}
    QTabWidget::pane {{
        border: 1px solid {c.border};
        border-radius: 10px;
        background-color: {c.surface};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 8px 14px;
        color: {c.text_muted};
        font-size: 13px;
    }}
    QTabBar::tab:selected {{
        color: {c.accent};
        border-bottom-color: {c.accent};
        font-weight: 600;
    }}
    QTabBar::tab:hover {{
        color: {c.text};
    }}

    QListWidget#FileList {{
        background-color: transparent;
        border: none;
        outline: none;
        padding: 2px;
    }}
    QListWidget {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 8px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 6px;
        border-radius: 6px;
        color: {c.text};
    }}
    QListWidget::item:selected {{
        background-color: {c.selection_bg};
        color: {c.selection_text};
    }}
    QListWidget#FileList::item {{
        border-radius: 8px;
        padding: 8px 10px;
        color: {c.text};
    }}
    QListWidget#FileList::item:hover {{
        background-color: {c.surface_hover};
    }}
    QListWidget#FileList::item:selected {{
        background-color: {c.selection_bg};
        color: {c.selection_text};
    }}

    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        margin: 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c.border};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c.text_muted};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        margin: 2px 4px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c.border};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}

    QProgressBar {{
        background-color: {c.progress_track};
        border: none;
        border-radius: 4px;
        min-height: 8px;
        max-height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {c.accent};
        border-radius: 4px;
    }}

    QSplitter::handle {{
        background-color: transparent;
    }}
    QStatusBar {{
        background-color: {c.surface};
        border-top: 1px solid {c.border};
        color: {c.text_muted};
        font-size: 12px;
    }}
    QStatusBar::item {{
        border: none;
    }}
    QDialog {{
        background-color: {c.bg};
    }}
    QMenu {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 18px;
        border-radius: 6px;
        color: {c.text};
    }}
    QMenu::item:selected {{
        background-color: {c.selection_bg};
        color: {c.selection_text};
    }}
    QToolTip {{
        background-color: {c.surface};
        color: {c.text};
        border: 1px solid {c.border};
        padding: 4px 8px;
    }}
    """
