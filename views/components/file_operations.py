import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QTimer
from models.config_manager import ConfigManager
from models.file_loader import FileLoaderThread

class FileOperations:
    MAX_BACKUPS_PER_FILE = 3  # Mantém apenas os últimos 3 backups por arquivo
    AUTO_SAVE_DEBOUNCE_MS = 5000  # Aguarda 5 segundos de inatividade antes de auto-salvar

    def __init__(self, main_window):
        self.main_window = main_window
        self.config = ConfigManager()
        self.loader_thread = None
        # Timer para debounce de auto-save (evita múltiplas gravações em sequência)
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self._execute_auto_save)

    def load_file(self, file_path=None):
        """Carrega um arquivo Excel, seja via diálogo ou caminho direto"""
        if not file_path:
            file_path = self._get_file_path_from_dialog()
        if not file_path or not os.path.exists(file_path):
            if file_path:
                self._remove_missing_file_from_recent(file_path)
            return False

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

        if getattr(self.main_window, 'current_file', None):
            return self._save_and_notify(self.main_window.current_file, create_backup=True, show_messages=True)
        return self.save_file_as()

    def auto_save(self):
        """Agenda auto-save com debounce (evita múltiplas gravações seguidas)"""
        # Valida se há um arquivo carregado
        if not getattr(self.main_window, 'current_file', None):
            self.main_window.logger.debug("Auto-save ignorado: nenhum arquivo carregado")
            return False

        if not self._validate_data_to_save():
            return False

        # Reinicia o timer de debounce
        self.auto_save_timer.stop()
        self.auto_save_timer.start(self.AUTO_SAVE_DEBOUNCE_MS)
        return True

    def _execute_auto_save(self):
        """Executa o auto-save efetivamente (chamado pelo timer de debounce)"""
        if not getattr(self.main_window, 'current_file', None):
            return False

        if not self._validate_data_to_save():
            return False

        # Salva sem criar backup e sem mostrar mensagens
        success = self._save_and_notify(self.main_window.current_file, create_backup=False, show_messages=False)
        if success:
            self.main_window.logger.debug(f"Auto-save concluído: {self.main_window.current_file}")
        return success

    def save_file_as(self):
        """Salva como novo arquivo"""
        if not self._validate_data_to_save():
            return False

        last_path = self.config.get_last_path()
        initial_dir = os.path.dirname(last_path) if last_path else ""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Salvar Como",
            initial_dir,
            "Feather Files (*.feather)"
        )
        if not file_path:
            return False
        if not file_path.endswith('.feather'):
            file_path += '.feather'

        self.config.set_last_path(file_path)
        self.main_window.current_file = file_path
        return self._save_and_notify(file_path, create_backup=True, show_messages=True)

    def _save_and_notify(self, file_path, create_backup=True, show_messages=True):
        """Salva o arquivo e opcionalmente exibe mensagens apropriadas

        Args:
            file_path: Caminho do arquivo a salvar
            create_backup: Se True, cria backup antes de salvar
            show_messages: Se True, mostra caixas de diálogo com mensagens
        """
        try:
            if create_backup:
                if not self._create_backup(file_path):
                    if show_messages:
                        QMessageBox.warning(self.main_window, "Aviso", "Não foi possível criar backup do arquivo.")

            success = self.main_window.excel_manager.save_excel(file_path)
            if success:
                if show_messages:
                    QMessageBox.information(self.main_window, "Sucesso", f"Arquivo salvo em:\n{file_path}")
                    self._show_post_save_message()
                self.main_window.logger.debug(f"Arquivo salvo com sucesso: {file_path}")
                return True
            else:
                if show_messages:
                    QMessageBox.critical(self.main_window, "Erro", "Falha ao salvar arquivo.")
                self.main_window.logger.error(f"Falha ao salvar arquivo: {file_path}")
                return False
        except Exception as e:
            self.main_window.logger.error(f"Erro ao salvar arquivo: {str(e)}")
            if show_messages:
                QMessageBox.critical(self.main_window, "Erro", f"Falha ao salvar:\n{str(e)}")
            return False

    def _create_backup(self, file_path):
        """Cria backup do arquivo antes de salvar e remove backups antigos"""
        backup_dir = os.path.join("resources", "backup")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_{os.path.basename(file_path)}"
        backup_path = os.path.join(backup_dir, backup_name)

        try:
            shutil.copy2(file_path, backup_path)
            self.main_window.logger.debug(f"Backup criado: {backup_path}")

            # Limpa backups antigos do mesmo arquivo
            self._cleanup_old_backups(backup_dir, file_path)
            return True
        except Exception as e:
            self.main_window.logger.error(f"Erro ao criar backup: {str(e)}")
            return False

    def _cleanup_old_backups(self, backup_dir, original_file_path):
        """Remove backups antigos, mantendo apenas os últimos MAX_BACKUPS_PER_FILE"""
        try:
            original_name = os.path.basename(original_file_path)
            # Encontra todos os backups deste arquivo
            backups = [
                f for f in os.listdir(backup_dir)
                if f.endswith(original_name) and f.startswith("backup_")
            ]

            # Se há mais backups que o limite, remove os mais antigos
            if len(backups) > self.MAX_BACKUPS_PER_FILE:
                # Ordena por timestamp (mais antigos primeiro)
                backups.sort()
                to_remove = backups[:len(backups) - self.MAX_BACKUPS_PER_FILE]

                for backup in to_remove:
                    backup_path = os.path.join(backup_dir, backup)
                    try:
                        os.remove(backup_path)
                        self.main_window.logger.debug(f"Backup removido: {backup_path}")
                    except Exception as e:
                        self.main_window.logger.warning(f"Falha ao remover backup {backup}: {str(e)}")
        except Exception as e:
            self.main_window.logger.warning(f"Erro ao limpar backups antigos: {str(e)}")

    def _show_post_save_message(self):
        """Exibe mensagem após salvar, mantendo contexto anterior se necessário"""
        record_count = len(self.main_window.excel_manager.df)
        prev_msg = getattr(self.main_window, '_previous_message', None)
        if prev_msg and "registros" in prev_msg[0]:
            prev_text = prev_msg[0]
            new_text = prev_text.split("Exibindo")[0] + f"Exibindo {record_count} registros"
            self.main_window.message_handler.show_message(new_text, "default")
        elif prev_msg:
            text, message_type = prev_msg
            self.main_window.message_handler.show_message(text, message_type)
        else:
            self.main_window.message_handler.show_record_count(record_count)

    def _get_file_path_from_dialog(self):
        """Abre diálogo para selecionar arquivo"""
        last_path = self.config.get_last_path()
        initial_dir = last_path if last_path else ""
        return QFileDialog.getOpenFileName(
            self.main_window,
            "Abrir Arquivo Feather",
            initial_dir,
            "Feather Files (*.feather)"
        )[0]

    def _remove_missing_file_from_recent(self, file_path):
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
            self.main_window.btn_del.setEnabled(success)

    def _handle_successful_load(self, file_path):
        """Atualiza UI após carregamento bem-sucedido"""
        if hasattr(self.main_window, 'command_manager'):
            self.main_window.command_manager.clear()
        self.main_window.current_file = file_path
        self.main_window._update_table()
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

    def get_recent_files(self):
        """Retorna a lista de arquivos recentes válidos (que ainda existem)"""
        recent_files = self.config.get_recent_files()
        valid_files = [f for f in recent_files if os.path.exists(f)]
        if len(valid_files) != len(recent_files):
            self.config.config["recent_files"] = valid_files
            self.config.save_config()
        return valid_files

    def cleanup_recent_files(self):
        """Remove arquivos inexistentes da lista de recentes"""
        return self.get_recent_files()