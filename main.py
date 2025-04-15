import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from utils.styles import (
    get_stylesheet,
    get_messagebox_stylesheet
)

def main():
    try:
        # Configuração inicial
        BASE_DIR = Path(__file__).parent
        os.chdir(BASE_DIR)
        sys.path.insert(0, str(BASE_DIR))

        # Cria aplicação
        app = QApplication(sys.argv)

        # Configura estilos iniciais
        app.setStyleSheet(get_stylesheet() + get_messagebox_stylesheet())

        # Import tardio para evitar problemas de recarregamento
        from views.main_window import MainWindow
        window = MainWindow()
        window.show()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"Erro crítico: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()