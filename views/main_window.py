import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableView, QLineEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon
from models.excel_manager import ExcelManager
from models.file_loader import FileLoaderThread
from models.search_manager import SearchManager
from utils.styles import apply_theme, load_theme_preference
from utils.ui_helpers import CenterWindowMixin, add_shadow, MessageHandler
from views.window_manager import WindowManager
from views.components.menu import MenuManager
from views.components.table import TableManager
from views.components.file_operations import FileOperations
MESSAGE_TIMEOUT = 3000  # 3 segundos

class MainWindow(QMainWindow, CenterWindowMixin):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando MainWindow...")

        self.current_theme = 'light'
        self.excel_manager = ExcelManager()
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
            self.btn_save = QPushButton("  Salvar")
            self.btn_save.setIcon(QIcon("assets/images/save_icon_white.png"))

            self.btn_add.setCursor(Qt.PointingHandCursor)
            self.btn_save.setCursor(Qt.PointingHandCursor)
            self.btn_add.setEnabled(False)
            self.btn_save.setEnabled(False)

            toolbar.addWidget(self.btn_add)
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

            self.search_btn = QPushButton()
            self.search_btn.setIcon(QIcon("assets/images/lupa_icon_white.png"))
            self.search_btn.setObjectName("search_btn")
            self.search_btn.setCursor(Qt.PointingHandCursor)

            search_layout.addWidget(self.search_field)
            search_layout.addWidget(self.search_btn)
            content_layout.addLayout(search_layout)

            # Inicializa o MessageHandler na posição correta (índice 3)
            self.message_handler = MessageHandler(self.content_widget, content_layout)
            self.message_handler.init_message_widget(position=3)

            # Table
            self.table = QTableView()
            self.table_manager = TableManager(self.table)
            content_layout.addWidget(self.table)

            # Sombras
            elements_with_shadow = [
                self.btn_add,
                self.btn_save,
                self.search_btn,
                self.search_field,
                self.table
            ]
            for element in elements_with_shadow:
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
            self.btn_save.clicked.connect(self.file_ops.save_file)

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

            if not self._load_last_file():
                # Só mostra "Pronto para carregar dados" se não carregar arquivo automaticamente
                self.message_handler.set_default_message("Pronto para carregar dados")
                self.message_handler.show_default_message()
                self.logger.info("Nenhum arquivo recente encontrado para carregar automaticamente")

        except Exception as e:
            self.logger.error("Erro nas configurações iniciais", exc_info=True)
            raise

    def _update_table(self, data=None):
        if data is None:
            if hasattr(self.excel_manager, 'df'):
                data = self.excel_manager.df
            else:
                return

        self.table_manager.update_table(data)
        self._update_buttons_state()

    def _update_table_with_data(self, data):
        self.table_manager.update_table_with_data(data)

    def _on_header_clicked(self, logical_index):
        if logical_index == 1:
            current_order = self.table.horizontalHeader().sortIndicatorOrder()
            self.table.sortByColumn(logical_index, current_order)

    def _load_last_file(self):
        """Carrega último arquivo automaticamente em segundo plano"""
        from models.config_manager import ConfigManager
        config = ConfigManager()
        file_path = config.get_last_path()

        if file_path and os.path.exists(file_path):
            # Usar QTimer para carregar em segundo plano
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._async_load_file(file_path))
            return True
        return False

    def _async_load_file(self, file_path):
        """Inicia o carregamento do arquivo"""
        self.logger.info(f"Iniciando carregamento do arquivo: {file_path}")
        try:
            # Configura UI
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setVisible(True)
            self.message_handler.show_message("Carregando arquivo...", "loading")
            self.setEnabled(False)
            QApplication.processEvents()

            # Cria e inicia thread
            self.loader_thread = FileLoaderThread(self.excel_manager, file_path)
            self.loader_thread.finished.connect(self._on_file_loaded)
            self.loader_thread.start()

        except Exception as e:
            self.logger.error("Erro ao iniciar carregamento do arquivo", exc_info=True)
            raise

    def _on_file_loaded(self, success, file_path):
        """Finaliza o carregamento"""
        self.logger.info(f"Carregamento concluído. Sucesso: {success}")
        try:
            if success:
                # Atualiza interface
                self.current_file = file_path
                self._update_table()
                self.file_ops.config.add_recent_file(file_path)
                self.setWindowTitle(f"Gerenciador de RMs - {os.path.basename(file_path)}")

                # Feedback visual de conclusão
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
                self.message_handler.show_message("Carregamento completo", "loading", MESSAGE_TIMEOUT)
                self.logger.info(f"Arquivo {file_path} carregado com sucesso")

                # Configura a mensagem padrão APÓS carregar
                QTimer.singleShot(MESSAGE_TIMEOUT, self.search_manager.update_record_count_message)
            else:
                self.message_handler.show_message("Falha no carregamento", "loading", MESSAGE_TIMEOUT)
                # Define mensagem padrão para estado sem arquivo
                self.message_handler.set_default_message("Pronto para carregar dados")
                self.logger.warning(f"Falha ao carregar arquivo {file_path}")

        except Exception as e:
            self.logger.error("Erro no pós-carregamento", exc_info=True)

        finally:
            # Restaura UI
            QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
            self.setEnabled(True)
            self.loader_thread = None

    def _update_buttons_state(self):
        """Atualiza estado dos botões"""
        has_data = hasattr(self.excel_manager, 'df') and not self.excel_manager.df.empty
        self.btn_add.setEnabled(has_data)
        self.btn_save.setEnabled(has_data)

    def _handle_search_change(self, text):
        """Reage a mudanças no campo de busca"""
        if not text.strip():
            self.search_manager.restore_full_list()

    def _init_resources_dir(self):
        """Garante que o diretório de recursos existe"""
        os.makedirs("resources", exist_ok=True)

    def resizeEvent(self, event):
        """Ajusta layout ao redimensionar"""
        super().resizeEvent(event)
        content_width = min(self.width(), self.MAX_CONTENT_WIDTH)
        self.content_widget.setFixedWidth(content_width)
        self.table_manager.resize_columns()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()