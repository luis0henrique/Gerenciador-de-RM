import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableView, QLineEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from models.command_manager import CommandManager, RemoveStudentsCommand
from models.data_manager import DataManager
from models.excel_manager import ExcelManager
from models.search_manager import SearchManager
from utils.styles import apply_theme, load_theme_preference
from utils.ui_helpers import CenterWindowMixin, add_shadow, MessageHandler, update_shadows_on_theme_change, MESSAGE_DEFAULT
from views.window_manager import WindowManager
from views.components.menu import MenuManager
from views.components.table import TableManager
from views.components.file_operations import FileOperations

class MainWindow(QMainWindow, CenterWindowMixin):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando MainWindow...")

        self.current_theme = 'light'
        self.command_manager = CommandManager()
        self.command_manager.operation_started.connect(self._handle_operation_start)
        self.command_manager.operation_finished.connect(self._handle_operation_finish)
        self.excel_manager = ExcelManager()
        self.data_manager = DataManager(self.excel_manager)
        self.current_file = None

        try:
            # Inicializa os gerenciadores
            self.logger.debug("Criando FileOperations e MenuManager...")
            self.file_ops = FileOperations(self)
            self.menu_manager = MenuManager(self)
            self.window_manager = WindowManager(self)

            self._init_ui()
            self._connect_signals()

            # Inicializa o SearchManager após a UI estar pronta
            self.search_manager = SearchManager(self.excel_manager, self.table_manager, self.message_handler)

            # Carrega configurações iniciais
            self._init_settings()
            self.table_manager.main_window = self
            self.loader_thread = None
            self.logger.info("MainWindow inicializada com sucesso")

        except Exception as e:
            self.logger.error("Falha na inicialização da MainWindow", exc_info=True)
            raise

    def _init_ui(self):
        self.logger.debug("Iniciando configuração da UI...")
        try:
            self.setWindowTitle("Gerenciador de RMs")
            self.setWindowIcon(QIcon('assets/images/icon.png'))
            self.setMinimumSize(QSize(800, 750))
            self.MAX_CONTENT_WIDTH = 750

            # Widget principal
            main_widget = QWidget()
            self.setCentralWidget(main_widget)

            # Layout principal
            main_layout = QVBoxLayout(main_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # Área de conteúdo principal
            window_layout = QWidget()
            window_layout_layout = QHBoxLayout(window_layout)
            window_layout_layout.setContentsMargins(0, 0, 0, 0)
            window_layout_layout.addStretch(1)

            self.content_widget = QWidget()
            self.content_widget.setMaximumWidth(self.MAX_CONTENT_WIDTH)
            content_layout = QVBoxLayout(self.content_widget)
            content_layout.setContentsMargins(20, 5, 20, 5)

            # Menu
            self.logger.debug("Criando barra de menu...")
            self.menu_manager.create_menu_bar()

            # Toolbar
            toolbar = QHBoxLayout()
            self.btn_add = QPushButton(" Adicionar Aluno(a)")
            self.btn_add.setIcon(QIcon("assets/images/add_icon_white.png"))
            self.btn_add.setToolTip("Abre a janela para adicionar novos alunos")

            self.btn_undo = QPushButton(" Desfazer")
            self.btn_undo.setIcon(QIcon("assets/images/undo_icon_white.png"))
            self.btn_undo.setToolTip("Desfazer a última ação (Ctrl+Z)")

            self.btn_redo = QPushButton(" Refazer")
            self.btn_redo.setIcon(QIcon("assets/images/redo_icon_white.png"))
            self.btn_redo.setToolTip("Refazer a última ação desfeita (Ctrl+Y)")

            self.btn_del = QPushButton("  Excluir")
            self.btn_del.setIcon(QIcon("assets/images/del_icon_white.png"))
            self.btn_del.setToolTip("Excluir alunos selecionados")

            self.btn_save = QPushButton("  Salvar")
            self.btn_save.setIcon(QIcon("assets/images/save_icon_white.png"))
            self.btn_save.setToolTip("Salva as alterações no arquivo atual e cria Backups")

            # Configuração do cursor
            for btn in [self.btn_add, self.btn_undo, self.btn_redo, self.btn_del, self.btn_save]:
                btn.setCursor(Qt.PointingHandCursor)

            # Estado inicial
            self.btn_add.setEnabled(False)
            self.btn_undo.setEnabled(False)
            self.btn_redo.setEnabled(False)
            self.btn_del.setEnabled(False)
            self.btn_save.setEnabled(False)

            toolbar.addStretch()
            toolbar.addWidget(self.btn_add)
            toolbar.addWidget(self.btn_del)
            toolbar.addWidget(self.btn_undo)
            toolbar.addWidget(self.btn_redo)
            toolbar.addWidget(self.btn_save)
            toolbar.addStretch()
            content_layout.addLayout(toolbar)

            # Search
            search_layout = QHBoxLayout()
            search_layout.setSpacing(0)
            search_layout.setContentsMargins(0, 0, 0, 0)

            self.search_field = QLineEdit()
            self.search_field.setObjectName("search_field")
            self.search_field.setPlaceholderText("Buscar por nome ou RM...")
            self.search_field.setToolTip("Digite parte do nome ou RM e pressione Enter ou clique na lupa para pesquisar")

            self.search_btn = QPushButton()
            self.search_btn.setIcon(QIcon("assets/images/lupa_icon_white.png"))
            self.search_btn.setObjectName("search_btn")
            self.search_btn.setToolTip("Executar busca")
            self.search_btn.setCursor(Qt.PointingHandCursor)

            search_layout.addWidget(self.search_field)
            search_layout.addWidget(self.search_btn)
            content_layout.addLayout(search_layout)

            # Inicializa o MessageHandler na posição correta (índice 3)
            self.message_handler = MessageHandler(self.content_widget, content_layout)

            # Table
            self.table = QTableView()
            self.table_manager = TableManager(self.table, self.message_handler)
            content_layout.addWidget(self.table)

            # Sombras
            self.elements_with_shadow = [
                self.btn_add,
                self.btn_save,
                self.btn_del,
                self.search_btn,
                self.search_field,
                self.table,
                self.message_handler.message_widget
            ]
            for element in self.elements_with_shadow:
                add_shadow(element)

            window_layout_layout.addWidget(self.content_widget)
            window_layout_layout.addStretch(1)
            main_layout.addWidget(window_layout, 1)

            # Progress bar
            self.progress_widget = QWidget()
            self.progress_widget.setFixedHeight(20)
            progress_layout = QHBoxLayout(self.progress_widget)
            progress_layout.setContentsMargins(0, 0, 0, 5)

            self.progress_bar = QProgressBar()
            self.progress_bar.setFixedWidth(700)
            self.progress_bar.setFixedHeight(16)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setVisible(False)

            progress_layout.addStretch()
            progress_layout.addWidget(self.progress_bar)
            progress_layout.addStretch()

            main_layout.addWidget(self.progress_widget)
            self.centralWidget().installEventFilter(self)

            # Aplica tema
            self.logger.debug("Aplicando tema...")
            apply_theme(QApplication.instance(), load_theme_preference())
            self.center_window()
            self.logger.info("UI configurada com sucesso")

        except Exception as e:
            self.logger.error("Erro na configuração da UI", exc_info=True)
            raise

    def _connect_signals(self):
        self.logger.debug("Conectando sinais...")
        try:
            self.btn_add.clicked.connect(self.window_manager.open_add_aluno_window)
            self.btn_del.clicked.connect(self._handle_delete_action)
            self.btn_undo.clicked.connect(self._handle_undo_action)
            self.btn_redo.clicked.connect(self._handle_redo_action)
            self.btn_save.clicked.connect(self.file_ops.save_file)

            # Atalhos de teclado
            self.btn_add.setShortcut("Ctrl+A")
            self.btn_del.setShortcut("Delete")
            self.btn_undo.setShortcut("Ctrl+Z")
            self.btn_redo.setShortcut("Ctrl+Y")
            self.btn_redo.setShortcut("Ctrl+S")

            self.search_btn.clicked.connect(lambda: self.search_manager.search_student(self.search_field.text()))
            self.search_field.returnPressed.connect(lambda: self.search_manager.search_student(self.search_field.text()))
            self.search_field.textChanged.connect(self._handle_search_change)

            # Configura o cabeçalho para ordenação
            header = self.table.horizontalHeader()
            header.setSortIndicatorShown(True)
            header.sectionClicked.connect(self._on_header_clicked)
            self.logger.debug("Sinais conectados com sucesso")

        except Exception as e:
            self.logger.error("Erro ao conectar sinais", exc_info=True)
            raise

    def _init_settings(self):
        self.logger.debug("Iniciando configurações...")
        try:
            self._init_resources_dir()

            if not self.file_ops.load_last_file():
                self.logger.info("Nenhum arquivo recente encontrado para carregar automaticamente")

        except Exception as e:
            self.logger.error("Erro nas configurações iniciais", exc_info=True)
            raise

    def update_ui_on_theme_change(self):
        """Atualiza elementos da UI quando o tema muda."""
        elements_with_shadow = [
            self.btn_add,
            self.btn_save,
            self.btn_del,
            self.search_btn,
            self.search_field,
            self.table,
            self.message_handler.message_widget
        ]
        update_shadows_on_theme_change(elements_with_shadow)

    def _update_table(self, data=None):
        if data is None:
            if hasattr(self.excel_manager, 'df'):
                data = self.excel_manager.df
            else:
                return

        self.table_manager.update_table(data)
        self._update_buttons_state()

        # Atualiza a mensagem padrão com a contagem atual de registros
        if hasattr(self.excel_manager, 'df'):
            count = len(self.excel_manager.df)
            self.message_handler.set_default_message(f"Exibindo {count} registros", MESSAGE_DEFAULT)

    def _update_table_with_data(self, data):
        self.table_manager.update_table_with_data(data)

    def _on_header_clicked(self, logical_index):
        if logical_index == 1:
            current_order = self.table.horizontalHeader().sortIndicatorOrder()
            self.table.sortByColumn(logical_index, current_order)

    def _update_buttons_state(self):
        """Atualiza estado dos botões"""
        has_data = hasattr(self.excel_manager, 'df') and not self.excel_manager.df.empty
        self.btn_add.setEnabled(has_data)
        self.btn_save.setEnabled(has_data)
        self.btn_del.setEnabled(has_data)
        self.btn_undo.setEnabled(len(self.command_manager.undo_stack) > 0)
        self.btn_redo.setEnabled(len(self.command_manager.redo_stack) > 0)

    def _handle_search_change(self, text):
        """Reage a mudanças no campo de busca"""
        if not text.strip():
            self.search_manager.restore_full_list()

    def _handle_delete_action(self):
        """Manipula a ação de exclusão de alunos de forma assíncrona"""
        if not hasattr(self, 'table_manager') or not self.table.selectedIndexes():
            self.message_handler.show_message("Nenhuma linha selecionada para exclusão", "warning")
            return

        selected_data = self.table_manager.get_selected_rows_data()
        remove_command = RemoveStudentsCommand(
            self.excel_manager,
            self.data_manager,
            selected_data
        )
        self.command_manager.execute_command(remove_command)

    def _handle_undo_action(self):
        """Manipula a ação de desfazer de forma assíncrona"""
        self.command_manager.undo()

    def _handle_redo_action(self):
        """Manipula a ação de refazer de forma assíncrona"""
        self.command_manager.redo()

    def _handle_operation_start(self, message):
        """Mostra mensagem quando uma operação começa"""
        self.message_handler.show_message(message, "loading")
        self._set_ui_enabled(False)  # Desabilita UI durante operação

    def _handle_operation_finish(self, success, message):
        """Lida com o fim de uma operação"""
        self._set_ui_enabled(True)
        if success:
            self._update_table()
            self.message_handler.show_temporary_message(message, "success")
        else:
            self.message_handler.show_message(message, "error")

    def _set_ui_enabled(self, enabled):
        """Habilita/desabilita controles da UI"""
        self.btn_add.setEnabled(enabled)
        self.btn_undo.setEnabled(enabled and len(self.command_manager.undo_stack) > 0)
        self.btn_redo.setEnabled(enabled and len(self.command_manager.redo_stack) > 0)
        self.btn_del.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        self.table.setEnabled(enabled)

    def _init_resources_dir(self):
        """Garante que o diretório de recursos existe para carregar e salvar os arquivos"""
        os.makedirs("resources", exist_ok=True)

    def resizeEvent(self, event):
        """Ajusta layout ao redimensionar"""
        super().resizeEvent(event)
        if event.oldSize().width() != event.size().width():
            content_width = min(self.width(), self.MAX_CONTENT_WIDTH)
            self.content_widget.setFixedWidth(content_width)
            self.table_manager.resize_columns()

    def eventFilter(self, obj, event):
        """Filtra eventos para desselecionar a tabela quando clicar fora"""
        if event.type() == event.MouseButtonPress:
            if not self.table.underMouse():
                self.table_manager.clear_selection()

        return super().eventFilter(obj, event)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()