from PyQt5.QtWidgets import QApplication, QHeaderView, QMenu, QAction, QTableView
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor

class TableManager:
    def __init__(self, table_view):
        self.table = table_view
        self.proxy_model = NumericSortProxyModel()
        self.CHUNK_SIZE = 1000
        self.current_chunk = 0
        self.is_loading = False
        self.full_data = None
        self.search_active = False

        self._setup_table()
        self._setup_context_menu()
        self._setup_scroll_connection()

    def _setup_table(self):
        self.table.setSortingEnabled(True)
        self.table.setCornerButtonEnabled(False)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows) # !!Quebra a lógica de copiar RM!!

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])
        self.proxy_model.setSourceModel(model)
        self.table.setModel(self.proxy_model)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        # header.setMinimumSectionSize(85)
        header.setDefaultAlignment(Qt.AlignCenter)
        # header.setStretchLastSection(False)
        header.resizeSection(0, 550)
        header.resizeSection(1, 100)

    def update_table(self, data, sort_column=1, sort_order=Qt.DescendingOrder):
        if data is None or data.empty:
            return

        self.full_data = data.sort_values('RM', ascending=False)
        self.current_chunk = 0
        self.search_active = False

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])
        self.proxy_model.setSourceModel(model)

        self._load_data_chunk()
        self.table.sortByColumn(sort_column, sort_order)

    def update_table_with_data(self, data):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])

        for _, row in data.iterrows():
            nome_item = QStandardItem(str(row['Nome do(a) Aluno(a)']))

            formatted_rm = "{:,.0f}".format(row['RM']).replace(",", ".")
            rm_item = QStandardItem(formatted_rm)
            rm_item.setData(int(row['RM']), Qt.UserRole)

            font = QFont()
            font.setBold(True)
            rm_item.setForeground(QColor(Qt.red))
            rm_item.setFont(font)
            rm_item.setTextAlignment(Qt.AlignCenter)

            model.appendRow([nome_item, rm_item])

        self.proxy_model.setSourceModel(model)
        self.search_active = True

    def _load_data_chunk(self):
        if self.is_loading or self.full_data is None or self.full_data.empty:
            return

        self.is_loading = True

        try:
            start = self.current_chunk * self.CHUNK_SIZE
            end = start + self.CHUNK_SIZE
            chunk = self.full_data.iloc[start:end]

            model = self.proxy_model.sourceModel()
            for _, row in chunk.iterrows():
                nome_item = QStandardItem(str(row['Nome do(a) Aluno(a)']))

                formatted_rm = "{:,.0f}".format(row['RM']).replace(",", ".")
                rm_item = QStandardItem(formatted_rm)
                rm_item.setData(int(row['RM']), Qt.UserRole)

                font = QFont()
                font.setBold(True)
                rm_item.setForeground(QColor(Qt.red))
                rm_item.setFont(font)
                rm_item.setTextAlignment(Qt.AlignCenter)

                model.appendRow([nome_item, rm_item])

            self.current_chunk += 1

            # Atualiza status bar com porcentagem
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'statusBar'):
                loaded = min(self.current_chunk * self.CHUNK_SIZE, len(self.full_data))
                percent = int((loaded / len(self.full_data)) * 100)
                self.main_window.statusBar().showMessage(
                    f"Carregados {loaded} de {len(self.full_data)} registros ({percent}%)", 3000
                )
        except Exception as e:
            print(f"Erro ao carregar chunk: {e}")
        finally:
            self.is_loading = False

    def _setup_scroll_connection(self):
        self.scroll_connection = self.table.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def _on_scroll(self, value):
        if (self.is_loading or self.full_data is None or
            self.search_active or not hasattr(self, 'full_data')):
            return

        scroll_bar = self.table.verticalScrollBar()
        at_bottom = value >= scroll_bar.maximum() * 0.8

        if at_bottom:
            loaded = self.current_chunk * self.CHUNK_SIZE
            total = len(self.full_data)

            if loaded < total:
                self._load_data_chunk()

    def _setup_context_menu(self):
        """Configura menu de contexto"""
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.copy_action = QAction("Copiar", self.table)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(self.copy_cell_content)  # Adiciona esta linha
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, position):
        """Mostra menu de contexto"""
        if self.table.selectedIndexes():
            menu = QMenu(self.table)
            menu.addAction(self.copy_action)
            menu.exec_(self.table.viewport().mapToGlobal(position))

    def copy_cell_content(self):
        """Copia conteúdo da célula selecionada"""
        selected = self.table.selectedIndexes()
        if selected:
            clipboard = QApplication.clipboard()
            text = selected[0].data(Qt.DisplayRole)
            clipboard.setText(str(text))

            # Feedback visual seguro
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage("Conteúdo copiado!", 2000)
            return True
        return False

    def resize_columns(self):
        total_width = self.table.viewport().width()
        rm_width = self.table.columnWidth(1)
        nome_width = max(200, total_width - rm_width)
        self.table.setColumnWidth(0, nome_width)

class NumericSortProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        if left.column() == 1:
            left_data = self.sourceModel().data(left, Qt.UserRole)
            right_data = self.sourceModel().data(right, Qt.UserRole)
            if left_data is not None and right_data is not None:
                return left_data < right_data
        return super().lessThan(left, right)