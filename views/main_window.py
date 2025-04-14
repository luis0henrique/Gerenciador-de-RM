import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableView, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from models.excel_manager import ExcelManager
from utils.helpers import remove_acentos
from utils.styles import (
    apply_theme, load_theme_preference,
)
from views.components import TableManager
from views.components.menu import MenuManager
from views.components.file_operations import FileOperations
from utils.ui_helpers import CenterWindowMixin, add_shadow

class MainWindow(QMainWindow, CenterWindowMixin):
    def __init__(self):
        super().__init__()
        self.current_theme = 'light'
        self.excel_manager = ExcelManager()
        self.current_file = None

        # Inicializa os gerenciadores
        self.file_ops = FileOperations(self)
        self.menu_manager = MenuManager(self)

        self._init_ui()
        self._connect_signals()

        # Carrega configurações iniciais
        self._init_settings()
        self.table_manager.main_window = self

    def _init_ui(self):
        self.setWindowTitle("Gerenciador de RMs")
        self.setWindowIcon(QIcon('assets/images/icon.png'))
        self.setMinimumSize(QSize(800, 750))
        self.MAX_CONTENT_WIDTH = 750

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        apply_theme(QApplication.instance(), load_theme_preference())

        window_layout = QHBoxLayout(central_widget)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)

        self.content_widget = QWidget()
        window_layout.addStretch(1)
        window_layout.addWidget(self.content_widget)
        window_layout.addStretch(1)

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 5, 20, 20)

        self.menu_manager.create_menu_bar()

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_load = QPushButton("Carregar Arquivo")
        self.btn_add = QPushButton(" Adicionar Aluno(a)")
        self.btn_add.setIcon(QIcon("assets/images/add_icon_white.png"))
        self.btn_save = QPushButton("  Salvar")
        self.btn_save.setIcon(QIcon("assets/images/save_icon_white.png"))

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

        search_layout.addWidget(self.search_field)
        search_layout.addWidget(self.search_btn)
        content_layout.addLayout(search_layout)

        # Table
        self.table = QTableView()
        self.table_manager = TableManager(self.table)
        self.table_manager.status_bar = self.statusBar
        content_layout.addWidget(self.table)

        for btn in [self.btn_load, self.btn_add, self.btn_save, self.search_btn]:
            add_shadow(btn)

        add_shadow(self.search_field)
        add_shadow(self.table)

        # Status bar
        self.status_bar = self.statusBar()

        self.center_window()  # Centraliza a janela

    def _connect_signals(self):
        self.btn_load.clicked.connect(self.file_ops.load_file)
        self.btn_add.clicked.connect(self._open_add_aluno_window)
        self.btn_save.clicked.connect(self.file_ops.save_file)

        self.search_btn.clicked.connect(self._search_student)
        self.search_field.returnPressed.connect(self._search_student)
        self.search_field.textChanged.connect(self._handle_search_change)

        # Configura o cabeçalho para ordenação
        header = self.table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self._on_header_clicked)

    def _init_settings(self):
        self._init_resources_dir()
        self.file_ops.load_recent_files()

        # Carrega o tema preferido
        from utils.styles import apply_theme
        self.current_theme = apply_theme(QApplication.instance(), load_theme_preference() or 'light')
        if not self._load_last_file():
            self.status_bar.showMessage("Pronto para carregar arquivo")

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

    def _search_student(self):
        search_term = self.search_field.text().strip()

        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            return

        if not search_term:
            self._restore_full_list()
            return

        normalized_term = remove_acentos(search_term.lower())

        if normalized_term.isdigit():
            result = self.excel_manager.df[self.excel_manager.df['RM'].astype(str) == normalized_term]
        else:
            mask = self.excel_manager.df['Nome do(a) Aluno(a)'].apply(
                lambda x: normalized_term in remove_acentos(str(x).lower()))
            result = self.excel_manager.df[mask]

        result_sorted = result.sort_values('Nome do(a) Aluno(a)')
        self._update_table_with_data(result_sorted)
        self.table.sortByColumn(0, Qt.AscendingOrder)

    def _restore_full_list(self):
        if hasattr(self.excel_manager, 'df'):
            self._update_table()
            self.status_bar.showMessage(f"Exibindo {len(self.excel_manager.df)} registros")

    def _on_header_clicked(self, logical_index):
        if logical_index == 1:
            current_order = self.table.horizontalHeader().sortIndicatorOrder()
            self.table.sortByColumn(logical_index, current_order)

    def _load_last_file(self):
        """Carrega último arquivo automaticamente em segundo plano"""
        last_path_file = os.path.join("resources", "last_path.dat")

        if os.path.exists(last_path_file):
            try:
                with open(last_path_file, "r") as f:
                    file_path = f.read().strip()

                if os.path.exists(file_path):
                    self.status_bar.showMessage(f"Carregando último arquivo...")

                    # Usar QTimer para carregar em segundo plano
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(100, lambda: self._async_load_file(file_path))
                    return True
            except Exception as e:
                print(f"Erro ao carregar último arquivo: {e}")

        return False

    def _async_load_file(self, file_path):
        """Carrega o arquivo de forma assíncrona"""
        try:
            QApplication.processEvents()  # Atualiza a UI

            if self.excel_manager.load_excel(file_path):
                self.current_file = file_path
                self._update_table()
                self.file_ops._add_recent_file(file_path)
                self.setWindowTitle(f"Gerenciador de RMs - {os.path.basename(file_path)}")
                self.status_bar.showMessage(f"Arquivo carregado: {os.path.basename(file_path)} - {len(self.excel_manager.df)} registros", 5000)
            else:
                self.status_bar.showMessage("Falha ao carregar arquivo", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Erro ao carregar arquivo: {str(e)}", 5000)
            print(f"Erro ao carregar arquivo: {e}")

    def _update_buttons_state(self):
        """Atualiza estado dos botões"""
        has_data = hasattr(self.excel_manager, 'df') and not self.excel_manager.df.empty
        self.btn_add.setEnabled(has_data)
        self.btn_save.setEnabled(has_data)

    def _handle_search_change(self, text):
        """Reage a mudanças no campo de busca"""
        if not text.strip():
            self._restore_full_list()

    def _open_add_aluno_window(self):
        from models.data_manager import DataManager
        from views.add_aluno import AddAlunoWindow

        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            QMessageBox.warning(self, "Aviso", "Carregue um arquivo primeiro")
            return

        try:
            data_manager = DataManager(self.excel_manager)
            self.add_window = AddAlunoWindow(self, data_manager)
            self.add_window.aluno_adicionado_signal.connect(self._update_table)
            self.add_window.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir janela:\n{str(e)}")

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