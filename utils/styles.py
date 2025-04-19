import os
from typing import Optional
from PyQt5.QtWidgets import QApplication
from models.config_manager import ConfigManager

config = ConfigManager()

def _read_css_file(theme_name: str) -> str:
    """Lê o arquivo CSS do tema especificado."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "themes", f"{theme_name}.css")

    try:
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo CSS do tema '{theme_name}' não encontrado: {css_path}")

def load_theme_preference() -> str:
    """Carrega a preferência de tema salva."""
    return config.get_theme() or 'light'  # Default para light

def apply_theme(app: QApplication, theme_name: Optional[str] = None) -> str:
    """Aplica o tema globalmente e persiste a preferência."""
    theme_name = theme_name or load_theme_preference()
    config.set_theme(theme_name)

    stylesheet = _read_css_file(theme_name)
    app.setStyleSheet(stylesheet)

    # Opcional: Atualiza widgets já existentes
    for widget in app.allWidgets():
        widget.setStyleSheet(stylesheet)

    return theme_name

def get_current_stylesheet() -> str:
    """Retorna a folha de estilo do tema atual."""
    return _read_css_file(load_theme_preference())

# Adicione estas funções ao final do arquivo styles.py (ou no local apropriado)
def get_stylesheet() -> str:
    """Retorna a folha de estilo do tema claro (para compatibilidade)."""
    return _read_css_file("light")

def get_dark_stylesheet() -> str:
    """Retorna a folha de estilo do tema escuro (para compatibilidade)."""
    return _read_css_file("dark")