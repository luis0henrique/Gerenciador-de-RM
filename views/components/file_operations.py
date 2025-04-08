import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class FileOperations:
    def __init__(self, main_window):
        self.main_window = main_window
        self.recent_files = []
        self.max_recent_files = 5

    def load_file(self, file_path=None):
        """Carrega um arquivo Excel"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "Abrir Arquivo Excel",
                "",
                "Excel Files (*.xlsx *.xls)"
            )

        if file_path:
            try:
                self.main_window.status_bar.showMessage(f"Carregando {os.path.basename(file_path)}...")

                if self.main_window.excel_manager.load_excel(file_path):
                    self.main_window.current_file = file_path
                    self.main_window._update_table()
                    self._add_recent_file(file_path)
                    self._save_last_path(file_path)
                    self.main_window.setWindowTitle(f"Gerenciador de RMs - {os.path.basename(file_path)}")

                    self.main_window.btn_add.setEnabled(True)
                    self.main_window.btn_save.setEnabled(True)
                    return True
                return False
            except Exception as e:
                QMessageBox.critical(self.main_window, "Erro", f"Falha ao carregar arquivo:\n{str(e)}")
                return False
        return False

    def _add_recent_file(self, file_path):
        """Adiciona arquivo à lista de recentes e salva no arquivo"""
        if not file_path or not os.path.exists(file_path):
            return

        if file_path in self.recent_files:
            self.recent_files.remove(file_path)

        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:self.max_recent_files]

        # Remove paths inválidos
        self.recent_files = [fp for fp in self.recent_files if os.path.exists(fp)]

        # Salva no arquivo
        os.makedirs("resources", exist_ok=True)
        with open(os.path.join("resources", "recent_files.dat"), 'w') as f:
            f.write("\n".join(self.recent_files))

    def _save_last_path(self, file_path):
        """Salva o último caminho acessado"""
        try:
            with open(os.path.join("resources", "last_path.dat"), "w") as f:
                f.write(file_path)
        except Exception as e:
            print(f"Erro ao salvar último caminho: {e}")

    def load_recent_files(self):
        """Carrega a lista de arquivos recentes"""
        recent_file_path = os.path.join("resources", "recent_files.dat")
        if os.path.exists(recent_file_path):
            with open(recent_file_path, 'r') as f:
                self.recent_files = [line.strip() for line in f if line.strip()]

    def load_recent_file(self, file_path):
        """Carrega um arquivo da lista de recentes"""
        try:
            if os.path.exists(file_path):
                return self.load_file(file_path)
            else:
                # Remove arquivo inexistente da lista
                if file_path in self.recent_files:
                    self.recent_files.remove(file_path)
                    self._add_recent_file("")  # Atualiza a lista
                return False
        except Exception as e:
            QMessageBox.critical(self.main_window, "Erro", f"Falha ao carregar arquivo recente:\n{str(e)}")
            return False

    def get_recent_files(self):
        """Retorna a lista de arquivos recentes válidos"""
        # Filtra apenas arquivos existentes
        valid_files = [fp for fp in self.recent_files if os.path.exists(fp)]

        # Se houve remoção de arquivos inválidos, atualiza a lista
        if len(valid_files) != len(self.recent_files):
            self.recent_files = valid_files
            self._add_recent_file("")  # Força a atualização do arquivo

        return self.recent_files

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
            "",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            self.main_window.current_file = file_path
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
            raise  # Propaga o erro para ser tratado pelo chamador