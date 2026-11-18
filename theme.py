"""
Tema de la interfaz (claro / oscuro / sistema).

Los estilos de la app fijan colores de fondo, así que cada esquema
necesita su propia hoja de estilo. ``apply_theme`` fija el esquema de Qt
(controles nativos, diálogos, menús) y aplica la hoja correspondiente a
toda la aplicación. En modo "sistema" se vuelve a aplicar cuando macOS
cambia de apariencia.

La preferencia se guarda con QSettings: con App Sandbox va a las
preferencias del contenedor, sin necesitar permisos extra.
"""

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication

THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"

THEME_LABELS = {
    THEME_SYSTEM: "Usar la del sistema",
    THEME_LIGHT: "Clara",
    THEME_DARK: "Oscura",
}

_SETTINGS_KEY = "appearance/theme"

# Colores del registro: tonos medios legibles sobre fondo claro y oscuro
# (las entradas ya escritas no cambian al cambiar de tema).
LOG_COLORS = {
    "timestamp": "#8b949e",
    "error": "#e5534b",
    "warning": "#d4880f",
    "success": "#2ea043",
    "info": "#3b8eea",
}

_PALETTES = {
    THEME_LIGHT: {
        "window": "#f5f5f5",
        "surface": "#ffffff",
        "surface_alt": "#f8f9fa",
        "tab": "#e0e0e0",
        "text": "#1d1d1f",
        "border": "#d0d0d0",
        "pane_border": "#c0c0c0",
        "grid": "#e0e0e0",
        "accent": "#007AFF",
        "accent_hover": "#0056CC",
        "disabled_bg": "#cccccc",
        "disabled_text": "#666666",
        "danger": "#e5484d",
        "danger_hover": "#c62a2f",
    },
    THEME_DARK: {
        "window": "#1e1e1e",
        "surface": "#2a2a2c",
        "surface_alt": "#232325",
        "tab": "#3a3a3c",
        "text": "#e8e8ea",
        "border": "#48484a",
        "pane_border": "#48484a",
        "grid": "#3a3a3c",
        "accent": "#0A84FF",
        "accent_hover": "#3d9bff",
        "disabled_bg": "#3a3a3c",
        "disabled_text": "#8e8e93",
        "danger": "#d93f45",
        "danger_hover": "#ff5a5f",
    },
}

_STYLESHEET = """
QMainWindow, QDialog, QToolBar, QStatusBar {{
    background-color: {window};
}}
QLabel, QCheckBox, QRadioButton, QStatusBar, QToolBar QToolButton {{
    color: {text};
}}
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    selection-background-color: {accent};
    selection-color: white;
}}
QTabWidget::pane {{
    border: 1px solid {pane_border};
    background-color: {surface};
    border-radius: 8px;
}}
QTabBar::tab {{
    background-color: {tab};
    color: {text};
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}
QTabBar::tab:selected {{
    background-color: {surface};
    border-bottom: 2px solid {accent};
}}
QPushButton {{
    background-color: {accent};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {accent_hover};
}}
QPushButton:disabled {{
    background-color: {disabled_bg};
    color: {disabled_text};
}}
QPushButton[danger="true"] {{
    background-color: {danger};
}}
QPushButton[danger="true"]:hover {{
    background-color: {danger_hover};
}}
QPushButton[danger="true"]:disabled {{
    background-color: {disabled_bg};
    color: {disabled_text};
}}
QListWidget {{
    border: 1px solid {border};
    border-radius: 6px;
    background-color: {surface};
    color: {text};
}}
QTableWidget {{
    border: 1px solid {border};
    border-radius: 6px;
    background-color: {surface};
    color: {text};
    gridline-color: {grid};
}}
QHeaderView::section {{
    background-color: {tab};
    color: {text};
    border: none;
    border-right: 1px solid {border};
    border-bottom: 1px solid {border};
    padding: 4px 6px;
}}
QGroupBox {{
    font-weight: bold;
    color: {text};
    border: 2px solid {border};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}}
QTextEdit#bucketInfo {{
    font-family: Monaco, monospace;
    font-size: 12px;
    padding: 10px;
    background-color: {surface_alt};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
}}
"""


def load_theme_preference() -> str:
    value = QSettings().value(_SETTINGS_KEY, THEME_SYSTEM)
    return value if value in THEME_LABELS else THEME_SYSTEM


def save_theme_preference(mode: str) -> None:
    QSettings().setValue(_SETTINGS_KEY, mode)


def _effective_scheme(app: QApplication, mode: str) -> str:
    if mode in (THEME_LIGHT, THEME_DARK):
        return mode
    hints = app.styleHints()
    if hasattr(hints, "colorScheme") and \
            hints.colorScheme() == Qt.ColorScheme.Dark:
        return THEME_DARK
    return THEME_LIGHT


def stylesheet_for(scheme: str) -> str:
    return _STYLESHEET.format(**_PALETTES[scheme])


_current_mode = THEME_SYSTEM
_listening = False


def apply_theme(app: QApplication, mode: str) -> None:
    """Aplica el tema elegido ("system", "light" o "dark")."""
    global _current_mode, _listening
    if mode not in THEME_LABELS:
        mode = THEME_SYSTEM
    _current_mode = mode

    hints = app.styleHints()
    # Qt >= 6.8: fija el esquema de los controles nativos; Unknown
    # devuelve el control al sistema.
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme({
            THEME_LIGHT: Qt.ColorScheme.Light,
            THEME_DARK: Qt.ColorScheme.Dark,
        }.get(mode, Qt.ColorScheme.Unknown))

    if not _listening and hasattr(hints, "colorSchemeChanged"):
        hints.colorSchemeChanged.connect(lambda _s: _refresh(app))
        _listening = True

    _refresh(app)


def _refresh(app: QApplication) -> None:
    app.setStyleSheet(stylesheet_for(_effective_scheme(app, _current_mode)))
