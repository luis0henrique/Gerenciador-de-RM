import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from utils.styles import (
    get_stylesheet, 
    get_messagebox_stylesheet,
    install_style_reloader
)

def main():
    try:
        # Configuração inicial
        BASE_DIR = Path(__file__).parent
        os.chdir(BASE_DIR)
        sys.path.insert(0, str(BASE_DIR))
        
        print("\n🟢 Iniciando aplicação...")
        
        # Cria aplicação
        app = QApplication(sys.argv)
        
        # Configura estilos iniciais
        app.setStyleSheet(get_stylesheet() + get_messagebox_stylesheet())
        
        # Instala o recarregador de estilos
        style_reloader = install_style_reloader(app)
        
        # Import tardio para evitar problemas de recarregamento
        from views.main_window import MainWindow
        window = MainWindow()
        window.show()
        
        print("\n🟢 Aplicação iniciada. Pressione F5 para recarregar estilos.")
        print("   Modifique o arquivo styles.py e pressione F5 para ver as mudanças.\n")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"🔴 Erro crítico: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()