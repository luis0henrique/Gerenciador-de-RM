from PyQt5.QtCore import QThread, pyqtSignal
import logging

class FileLoaderThread(QThread):
    finished = pyqtSignal(bool, str) # success, file_path
    progress = pyqtSignal(int) # progress percentage

    def __init__(self, excel_manager, file_path):
        super().__init__()
        self.excel_manager = excel_manager
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            success = self.excel_manager.load_excel(self.file_path)
            self.finished.emit(success, self.file_path)
        except Exception as e:
            self.logger.error("Erro no carregamento", exc_info=True)
            self.finished.emit(False, self.file_path)