import sys
import os
import logging
import argparse
from pathlib import Path
from PyQt5.QtWidgets import QApplication

def setup_logging(debug=False):
    """Configura o sistema de logging, limpando o arquivo a cada execução"""
    # Limpa o arquivo de log existente
    log_file = "app.log"
    with open(log_file, 'w'):
        pass

    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    setup_logging(debug=args.debug)
    setup_logging()
    logging.info("Iniciando configuração da aplicação...")
    try:
        # Configuração inicial
        BASE_DIR = Path(__file__).parent
        logging.debug(f"Diretório base definido como: {BASE_DIR}")
        os.chdir(BASE_DIR)
        sys.path.insert(0, str(BASE_DIR))

        # Cria aplicação
        logging.info("Criando QApplication...")
        app = QApplication(sys.argv)

        # Import tardio
        logging.info("Carregando a janela principal...")
        from views.main_window import MainWindow
        window = MainWindow()
        window.show()

        # Executa o loop principal do aplicativo
        exit_code = app.exec_()

        logging.info(f"Loop de eventos finalizado com código: {exit_code}")
        app.quit()
        sys.exit(exit_code)

    except Exception as e:
        logging.error("Falha durante a inicialização:", exc_info=True)
        if 'app' in locals():
            app.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()