import logging
from PyQt5.QtWidgets import QMessageBox
from models.data_manager import DataManager
from views.add_aluno import AddAlunoWindow

class WindowManager:
    def __init__(self, main_window):
        """
        Gerencia a abertura de janelas modais do sistema.
        :param main_window: Referência à MainWindow (para acesso a excel_manager, table_manager, etc.)
        """
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        self.add_aluno_window = None  # Referência à janela de adição

    def open_add_aluno_window(self):
        """Abre a janela de adição de alunos com validações e tratamento de erros."""
        try:
            self._validate_excel_loaded()
            data_manager = DataManager(self.main_window.excel_manager)
            self._setup_add_aluno_window(data_manager)
        except Exception as e:
            self._handle_window_error(e)

    def _validate_excel_loaded(self):
        """Valida se há dados carregados no excel_manager."""
        excel_manager = getattr(self.main_window, "excel_manager", None)
        if not excel_manager or not hasattr(excel_manager, "df") or excel_manager.df.empty:
            self.logger.warning("Tentativa de abrir janela sem arquivo carregado")
            QMessageBox.warning(self.main_window, "Aviso", "Carregue um arquivo primeiro")
            raise RuntimeError("Excel não carregado")

    def _setup_add_aluno_window(self, data_manager):
        """
        Configura e exibe a janela de adição de alunos, conectando todos os sinais necessários.
        Garante que apenas uma janela modal esteja aberta por vez.
        """
        # Evita múltiplas janelas abertas
        if self.add_aluno_window is not None and self.add_aluno_window.isVisible():
            self.add_aluno_window.raise_()
            self.add_aluno_window.activateWindow()
            return

        self.add_aluno_window = AddAlunoWindow(
            parent=self.main_window,
            data_manager=data_manager,
            excel_manager=self.main_window.excel_manager,
            command_manager=self.main_window.command_manager
        )

        # Conecta todos os sinais necessários
        self.add_aluno_window.aluno_adicionado_signal.connect(
            self.main_window.search_manager.restore_full_list
        )
        self.add_aluno_window.aluno_adicionado_signal.connect(
            self.main_window._update_table
        )
        self.add_aluno_window.aluno_adicionado_signal.connect(
            lambda: self.main_window.btn_save.setEnabled(True)
        )

        self.add_aluno_window.exec_()
        self.add_aluno_window = None  # Libera referência após fechar

    def _handle_window_error(self, error):
        """Trata erros genéricos de janela, exibindo mensagem ao usuário e logando detalhes."""
        self.logger.error(f"Erro na janela de adição: {str(error)}", exc_info=True)
        QMessageBox.critical(
            self.main_window,
            "Erro",
            f"Falha ao abrir janela:\n{str(error)}"
        )