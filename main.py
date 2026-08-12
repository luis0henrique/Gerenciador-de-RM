import sys
import os
import logging
import argparse
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QPixmap

# Constante de módulo — definida antes de qualquer inicialização
BASE_DIR = Path(__file__).resolve().parent


def enable_hi_dpi() -> None:
    """Configura suporte a High DPI antes da criação do QApplication."""
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # AA_UseHighDpiPixmaps já ativa o scaling automático; variáveis de
    # ambiente adicionais podem conflitar — mantemos apenas o necessário.
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


def setup_logging(debug: bool = False) -> None:
    """Configura o sistema de logging, limpando o arquivo a cada execução."""
    log_file = BASE_DIR / "app.log"
    log_file.write_text("")  # Limpa o arquivo anterior de forma segura

    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info(f"Python {sys.version} | Nível de log: {'DEBUG' if debug else 'INFO'}")


def show_splash(app: QApplication) -> QSplashScreen | None:
    """
    Exibe a splash screen durante o carregamento.
    Retorna None se a imagem não for encontrada, evitando crash.
    """
    splash_path = BASE_DIR / "assets" / "images" / "splash.png"
    if not splash_path.exists():
        logging.warning(f"Splash screen não encontrada em: {splash_path}")
        return None

    pixmap = QPixmap(str(splash_path)).scaled(
        555, 426, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()  # Garante que a splash seja renderizada imediatamente
    return splash


def main() -> None:
    """Ponto de entrada principal da aplicação."""
    # HiDPI deve ser configurado ANTES da criação do QApplication
    enable_hi_dpi()

    parser = argparse.ArgumentParser(description="Inicializador da aplicação")
    parser.add_argument("--debug", action="store_true", help="Ativa logging em modo debug")
    args = parser.parse_args()

    setup_logging(debug=args.debug)
    logging.info("Iniciando aplicação...")
    logging.debug(f"Diretório base: {BASE_DIR}")

    # Muda para o diretório base para que imports relativos funcionem corretamente
    os.chdir(BASE_DIR)
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    app = QApplication(sys.argv)
    splash = show_splash(app)

    try:
        # Import tardio intencional: MainWindow depende de QApplication já instanciada
        logging.info("Carregando janela principal...")
        from views.main_window import MainWindow

        window = MainWindow()
        window.show()

        if splash is not None:
            splash.finish(window)

        exit_code = app.exec_()
        logging.info(f"Aplicação encerrada com código: {exit_code}")

    except Exception:
        logging.critical("Falha crítica durante a inicialização:", exc_info=True)
        if splash is not None:
            splash.close()
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()