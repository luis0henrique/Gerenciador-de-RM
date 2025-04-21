import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QTimer
from models.config_manager import ConfigManager
from models.file_loader import FileLoaderThread

class FileOperations:
    def __init__(self, main_window):
        self.main_window = main_window
        self.config = ConfigManager()
        self.loader_thread = None

    def load_file(self, file_path=None):
        """Carrega um arquivo Excel, seja via diálogo ou caminho direto"""
        if not file_path:
            file_path = self._get_file_path_from_dialog()

        if not file_path:
            return False

        if not os.path.exists(file_path):
            self._handle_missing_file(file_path)
            return False

        # Atualiza last_path antes de começar o carregamento
        self.config.set_last_path(file_path)
        self._prepare_ui_for_loading()
        self._start_async_load(file_path)
        return True

    def load_last_file(self):
        """Tenta carregar o último arquivo usado automaticamente"""
        file_path = self.config.get_last_path()
        if file_path and os.path.exists(file_path):
            QTimer.singleShot(100, lambda: self.load_file(file_path))
            return True
        return False

    def save_file(self):
        """Salva o arquivo atual"""
        if not self._validate_data_to_save():
            return False

        if hasattr(self.main_window, 'current_file') and self.main_window.current_file:
            return self._save_to_existing_file()
        return self.save_file_as()

    def save_file_as(self):
        """Salva como novo arquivo"""
        if not self._validate_data_to_save():
            return False

        # Usa o diretório do last_path se existir, senão usa o padrão
        last_path = self.config.get_last_path()
        initial_dir = os.path.dirname(last_path) if last_path else ""

        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Salvar Como",
            initial_dir,
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return False

        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'

        # Atualiza last_path com caminho completo
        self.config.set_last_path(file_path)
        self.main_window.current_file = file_path
        return self._save_to_existing_file()

    # Métodos auxiliares privados
    def _get_file_path_from_dialog(self):
        """Abre diálogo para selecionar arquivo"""
        last_path = self.config.get_last_path()
        initial_dir = last_path if last_path else ""

        return QFileDialog.getOpenFileName(
            self.main_window,
            "Abrir Arquivo Excel",
            initial_dir,
            "Excel Files (*.xlsx *.xls)"
        )[0]

    def _handle_missing_file(self, file_path):
        """Remove arquivo inexistente da lista de recentes"""
        recent_files = self.config.get_recent_files()
        if file_path in recent_files:
            recent_files.remove(file_path)
            self.config.config["recent_files"] = recent_files
            self.config.save_config()
        QMessageBox.warning(self.main_window, "Aviso", f"Arquivo não encontrado:\n{file_path}")

    def _prepare_ui_for_loading(self):
        """Prepara a UI para o carregamento"""
        self.main_window.message_handler.show_loading()
        self.main_window.progress_bar.setRange(0, 0)
        self.main_window.progress_bar.setVisible(True)
        self.main_window.setEnabled(False)

    def _start_async_load(self, file_path):
        """Inicia o carregamento assíncrono do arquivo"""
        self.loader_thread = FileLoaderThread(self.main_window.excel_manager, file_path)
        self.loader_thread.finished.connect(lambda success: self._on_file_loaded(success, file_path))
        self.loader_thread.start()

    def _on_file_loaded(self, success, file_path):
        """Callback quando o carregamento termina"""
        try:
            if success:
                self._handle_successful_load(file_path)
            else:
                self._handle_failed_load(file_path)
        except Exception as e:
            self.main_window.logger.error("Erro no pós-carregamento", exc_info=True)
            self.main_window.message_handler.show_error("Erro ao processar arquivo. Veja o log.")
        finally:
            self._restore_ui_after_loading()

    def _handle_successful_load(self, file_path):
        """Atualiza UI após carregamento bem-sucedido"""
        self.main_window.current_file = file_path
        self.main_window._update_table()

        # Atualiza ambos: recent_files e last_path
        self.config.add_recent_file(file_path)
        self.config.set_last_path(file_path)

        self.main_window.setWindowTitle(f"Gerenciador de RMs - {os.path.basename(file_path)}")

        record_count = len(self.main_window.excel_manager.df)
        self.main_window.message_handler.show_record_count(record_count)

        self.main_window.progress_bar.setRange(0, 100)
        self.main_window.progress_bar.setValue(100)
        self.main_window.logger.info(f"Arquivo {file_path} carregado com sucesso")

    def _handle_failed_load(self, file_path):
        """Lida com falha no carregamento"""
        self.main_window.logger.warning(f"Falha ao carregar arquivo {file_path}")
        self.main_window.message_handler.show_error("Erro ao carregar o arquivo. Veja o log.")

    def _restore_ui_after_loading(self):
        """Restaura a UI após tentativa de carregamento"""
        QTimer.singleShot(500, lambda: self.main_window.progress_bar.setVisible(False))
        self.main_window.setEnabled(True)
        self.loader_thread = None

    def _validate_data_to_save(self):
        """Valida se há dados para salvar"""
        if not hasattr(self.main_window.excel_manager, 'df') or self.main_window.excel_manager.df.empty:
            QMessageBox.warning(self.main_window, "Aviso", "Nenhum dado carregado para salvar")
            return False
        return True

    def _save_to_existing_file(self):
        """Salva no arquivo atual"""
        try:
            self._create_backup(self.main_window.current_file)
            self.main_window.excel_manager.df.to_excel(self.main_window.current_file, index=False)
            QMessageBox.information(self.main_window, "Sucesso",
                                  f"Arquivo salvo em:\n{self.main_window.current_file}")
            return True
        except Exception as e:
            QMessageBox.critical(self.main_window, "Erro", f"Falha ao salvar:\n{str(e)}")
            return False

    def _create_backup(self, file_path):
        """Cria backup do arquivo antes de salvar"""
        backup_dir = os.path.join("resources", "backup")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_{os.path.basename(file_path)}"
        backup_path = os.path.join(backup_dir, backup_name)

        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            self.main_window.logger.error(f"Erro ao criar backup: {str(e)}")
            raise

    def get_recent_files(self):
        """Retorna a lista de arquivos recentes válidos (que ainda existem)"""
        recent_files = self.config.get_recent_files()
        # Filtra apenas arquivos que ainda existem
        valid_files = [f for f in recent_files if os.path.exists(f)]

        # Atualiza a lista no config se algum arquivo foi removido
        if len(valid_files) != len(recent_files):
            self.config.config["recent_files"] = valid_files
            self.config.save_config()

        return valid_files

    def cleanup_recent_files(self):
        """Remove arquivos inexistentes da lista de recentes"""
        valid_files = self.get_recent_files()  # Já faz a limpeza automaticamente
        return valid_files