import sys
import os
import logging
import argparse
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QPixmap

def show_splash():
    """Mostra uma splash screen durante o carregamento."""
    pixmap = QPixmap("assets/images/splash.png").scaled(555, 426, Qt.KeepAspectRatio)
    splash = QSplashScreen(pixmap)
    splash.show()
    QApplication.processEvents()  # Mantém a aplicação responsiva
    return splash

def setup_logging(debug=False):
    """Configura o sistema de logging, limpando o arquivo a cada execução."""
    log_file = "app.log"
    with open(log_file, 'w'):
        pass  # Limpa o arquivo de log existente

    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def enable_hi_dpi():
    """Configurações para suporte a High DPI."""
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

def main():
    """Função principal de inicialização da aplicação."""
    enable_hi_dpi()

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    setup_logging(debug=args.debug)
    logging.info("Iniciando configuração da aplicação...")

    app = None
    splash = None
    try:
        # Configuração inicial de diretório e path
        BASE_DIR = Path(__file__).parent
        logging.debug(f"Diretório base definido como: {BASE_DIR}")
        os.chdir(BASE_DIR)
        sys.path.insert(0, str(BASE_DIR))

        # Cria aplicação Qt
        logging.info("Criando QApplication...")
        app = QApplication(sys.argv)

        # Mostra splash screen
        splash = show_splash()

        # Import tardio da janela principal para evitar problemas de inicialização do Qt
        logging.info("Carregando a janela principal...")
        from views.main_window import MainWindow
        window = MainWindow()
        window.show()

        # Fecha o splash screen após exibir a janela principal
        if splash is not None:
            splash.finish(window)

        # Executa o loop principal do aplicativo
        exit_code = app.exec_()
        logging.info(f"Loop de eventos finalizado com código: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        logging.error("Falha durante a inicialização:", exc_info=True)
        sys.exit(1)
    finally:
        if app is not None:
            app.quit()

if __name__ == "__main__":
    main()