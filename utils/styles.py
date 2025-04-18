import os
from typing import Optional
from PyQt5.QtWidgets import QApplication
from models.config_manager import ConfigManager

config = ConfigManager()

def _read_css_section(section_name: str) -> str:
    """Lê uma seção específica do arquivo CSS usando marcadores."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "styles.css")

    try:
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()
            start_marker = f"/* $${section_name}_START$$ */"
            end_marker = f"/* $${section_name}_END$$ */"

            start_idx = content.find(start_marker)
            if start_idx == -1:
                return ""

            end_idx = content.find(end_marker, start_idx)
            if end_idx == -1:
                return ""

            return content[start_idx + len(start_marker):end_idx].strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo CSS não encontrado em: {css_path}")

def get_stylesheet() -> str:
    """Obtém a folha de estilo no tema claro (light)."""
    return _read_css_section("LIGHT")

def get_dark_stylesheet() -> str:
    """Obtém a folha de estilo no tema escuro (dark)."""
    return _read_css_section("DARK")

def load_theme_preference() -> str:
    """Carrega a preferência de tema salva"""
    return config.get_theme() or 'light'  # Default para light

def apply_theme(app: QApplication, theme_name: Optional[str] = None) -> str:
    """Aplica o tema globalmente e persiste a preferência"""
    theme_name = theme_name or load_theme_preference()
    config.set_theme(theme_name)

    # Seleciona a stylesheet apropriada
    stylesheet = get_dark_stylesheet() if theme_name == 'dark' else get_stylesheet()

    # Aplica a todos os widgets
    app.setStyleSheet(stylesheet)
    for widget in app.allWidgets():
        widget.setStyleSheet(stylesheet)

    return theme_name

def get_current_stylesheet() -> str:
    """Retorna a folha de estilo atual baseada na preferência salva"""
    theme = load_theme_preference()
    return get_dark_stylesheet() if theme == 'dark' else get_stylesheet()