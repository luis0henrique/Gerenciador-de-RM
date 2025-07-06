import os
from typing import Optional
from PyQt5.QtWidgets import QApplication
from models.config_manager import ConfigManager
from PyQt5.QtGui import QColor

config = ConfigManager()

def _read_css_file(theme_name: str) -> str:
    """Lê o arquivo CSS do tema especificado. Retorna string vazia se não encontrado."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "themes", f"{theme_name}.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Arquivo CSS do tema '{theme_name}' não encontrado: {css_path}")
        return ""  # Retorna vazio para evitar crash

def load_theme_preference() -> str:
    """Carrega a preferência de tema salva. Default para 'light'."""
    return config.get_theme() or 'light'

def apply_theme(app: QApplication, theme_name: Optional[str] = None) -> str:
    """
    Aplica o tema globalmente e persiste a preferência.
    Notifica widgets que implementam update_ui_on_theme_change.
    """
    theme_name = theme_name or load_theme_preference()
    config.set_theme(theme_name)
    stylesheet = _read_css_file(theme_name)
    app.setStyleSheet(stylesheet)

    # Notifica widgets que implementam update_ui_on_theme_change
    for widget in app.allWidgets():
        if hasattr(widget, 'update_ui_on_theme_change'):
            widget.update_ui_on_theme_change()
    return theme_name

def get_current_stylesheet() -> str:
    """Retorna a folha de estilo do tema atual."""
    return _read_css_file(load_theme_preference())

def get_stylesheet() -> str:
    """Retorna a folha de estilo do tema claro (para compatibilidade)."""
    return _read_css_file("light")

def get_dark_stylesheet() -> str:
    """Retorna a folha de estilo do tema escuro (para compatibilidade)."""
    return _read_css_file("dark")

def get_shadow_color(light_color=(85, 85, 85, 100), dark_color=(0, 0, 0, 100)) -> QColor:
    """
    Retorna a cor da sombra baseada no tema atual.
    Pode ser parametrizado para facilitar ajustes.
    """
    theme = load_theme_preference()
    rgba = light_color if theme == "light" else dark_color
    return QColor(*rgba)