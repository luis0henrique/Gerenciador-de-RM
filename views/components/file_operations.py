# views/components/file_operations.py
import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from models.config_manager import ConfigManager

class FileOperations:
    def __init__(self, main_window):
        self.main_window = main_window
        self.config = ConfigManager()

    def load_file(self, file_path=None):
        """Carrega um arquivo Excel"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "Abrir Arquivo Excel",
                self.config.get_last_path() or "",
                "Excel Files (*.xlsx *.xls)"
            )

        if file_path:
            try:
                self.main_window.status_bar.showMessage(f"Carregando {os.path.basename(file_path)}...")
                if self.main_window.excel_manager.load_excel(file_path):
                    self.main_window.current_file = file_path
                    self.main_window._update_table()
                    # Usa apenas o ConfigManager para salvar os caminhos
                    self.config.add_recent_file(file_path)
                    self.config.set_last_path(file_path)
                    self.main_window.setWindowTitle(f"Gerenciador de RMs - {os.path.basename(file_path)}")
                    self.main_window.btn_add.setEnabled(True)
                    self.main_window.btn_save.setEnabled(True)
                    return True
                return False
            except Exception as e:
                QMessageBox.critical(self.main_window, "Erro", f"Falha ao carregar arquivo:\n{str(e)}")
                return False
        return False

    def load_recent_file(self, file_path):
        """Carrega um arquivo da lista de recentes"""
        try:
            if os.path.exists(file_path):
                return self.load_file(file_path)
            else:
                # Remove arquivo inexistente da lista via ConfigManager
                recent_files = self.config.get_recent_files()
                if file_path in recent_files:
                    recent_files.remove(file_path)
                    self.config.config["recent_files"] = recent_files
                    self.config.save_config()
                return False
        except Exception as e:
            QMessageBox.critical(self.main_window, "Erro", f"Falha ao carregar arquivo recente:\n{str(e)}")
            return False

    def get_recent_files(self):
        """Retorna a lista de arquivos recentes válidos"""
        return self.config.get_recent_files()

    def save_file(self):
        """Salva o arquivo atual"""
        if not hasattr(self.main_window.excel_manager, 'df') or self.main_window.excel_manager.df.empty:
            QMessageBox.warning(self.main_window, "Aviso", "Nenhum dado carregado para salvar")
            return False

        if hasattr(self.main_window, 'current_file') and self.main_window.current_file:
            self._create_backup(self.main_window.current_file)
            file_path = self.main_window.current_file
        else:
            return self.save_file_as()

        try:
            self.main_window.excel_manager.df.to_excel(file_path, index=False)
            QMessageBox.information(self.main_window, "Sucesso", f"Arquivo salvo em:\n{file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self.main_window, "Erro", f"Falha ao salvar:\n{str(e)}")
            return False

    def save_file_as(self):
        """Salva como novo arquivo"""
        if not hasattr(self.main_window.excel_manager, 'df') or self.main_window.excel_manager.df.empty:
            QMessageBox.warning(self.main_window, "Aviso", "Nenhum dado carregado para salvar")
            return False

        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Salvar Como",
            self.config.get_last_path() or "",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            self.main_window.current_file = file_path
            # Atualiza o último caminho ao salvar como
            self.config.set_last_path(os.path.dirname(file_path))
            return self.save_file()
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
            print(f"Erro ao criar backup: {str(e)}")
            raise