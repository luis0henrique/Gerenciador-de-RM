import os
import json
import importlib
from PyQt5.QtCore import Qt, QObject

print("🔵 Módulo de estilos carregado inicialmente")

def force_reload_styles(app):
    """Força o recarregamento completo dos estilos"""
    try:
        print("\n🔵 Iniciando recarregamento de estilos...")

        # 1. Importa o módulo de forma absoluta
        import utils.styles as styles_module

        # 2. Limpa o cache de importação
        importlib.invalidate_caches()

        # 3. Recarrega o módulo
        styles_module = importlib.reload(styles_module)

        # 4. Aplica os novos estilos
        new_stylesheet = styles_module.get_stylesheet() + styles_module.get_messagebox_stylesheet()
        app.setStyleSheet(new_stylesheet)

        # 5. Atualiza todos os widgets
        for widget in app.allWidgets():
            if hasattr(widget, 'setStyleSheet'):
                widget.setStyleSheet(new_stylesheet)

        print("✅ Estilos recarregados com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro ao recarregar estilos: {repr(e)}")
        import traceback
        traceback.print_exc()
        return False

class StyleReloader(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress and event.key() == Qt.Key_F5:
            force_reload_styles(self.app)
            return True
        return super().eventFilter(obj, event)

def install_style_reloader(app):
    """Instala o recarregador de estilos na aplicação"""
    print("Instalando recarregador de estilos...")
    reloader = StyleReloader(app)
    app.installEventFilter(reloader)
    return reloader

def _read_css_section(section_name):
    """Lê uma seção específica do arquivo CSS usando marcadores."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "styles.css")

    try:
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()

            start_marker = f"/* $${section_name}_START$$ */"
            end_marker = f"/* $${section_name}_END$$ */"

            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker, start_idx)

            if start_idx == -1 or end_idx == -1:
                return ""

            return content[start_idx + len(start_marker):end_idx].strip()

    except FileNotFoundError:
        return ""

# Funções originais (mantidas para compatibilidade)
def get_stylesheet():
    return _read_css_section("LIGHT")

def get_dark_stylesheet():
    return _read_css_section("DARK")

def get_messagebox_stylesheet():
    return _read_css_section("MESSAGE_BOX")

# Funções auxiliares (mantidas conforme seu código original)
def load_theme_preference():
    """Carrega a preferência de tema salva"""
    try:
        theme_file = os.path.join("resources", "theme_preference.json")
        if os.path.exists(theme_file):
            with open(theme_file, 'r') as f:
                data = json.load(f)
                return data.get('theme', 'light')
        return 'light'
    except:
        return 'light'

def apply_theme(app, theme_name):
    """Aplica o tema globalmente e persiste a preferência"""
    theme_name = theme_name or 'light'  # Default
    save_theme_preference(theme_name)
    
    stylesheet = get_dark_stylesheet() if theme_name == 'dark' else get_stylesheet()
    app.setStyleSheet(stylesheet + get_messagebox_stylesheet())
    
    # Atualiza widgets existentes
    for widget in app.allWidgets():
        widget.setStyleSheet(stylesheet)
    
    return theme_name

def save_theme_preference(theme_name):
    """Salva a preferência de tema"""
    os.makedirs("resources", exist_ok=True)
    theme_file = os.path.join("resources", "theme_preference.json")
    with open(theme_file, 'w') as f:
        json.dump({'theme': theme_name}, f)

def get_current_stylesheet():
    """Retorna a folha de estilo atual baseada na preferência salva"""
    theme = load_theme_preference()
    if theme == 'dark':
        return get_dark_stylesheet()
    return get_stylesheet()