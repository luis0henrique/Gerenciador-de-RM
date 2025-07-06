from PyQt5.QtWidgets import QApplication, QHeaderView, QMenu, QAction, QTableView
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
from utils.ui_helpers import MESSAGE_SUCCESS
import string

class TableManager:
    def __init__(self, table_view, message_handler=None):
        self.table = table_view
        self.proxy_model = NumericSortProxyModel()
        self.CHUNK_SIZE = 1000
        self.current_chunk = 0
        self.is_loading = False
        self.full_data = None
        self.search_active = False
        self.message_handler = message_handler

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Sobrenome", "Nome do(a) Aluno(a)", "RM"])
        self.proxy_model.setSourceModel(self.model)
        self.table.setModel(self.proxy_model)
        self.model.itemChanged.connect(self._on_item_changed)

        self.current_letter = 'A'
        self.letters = list(string.ascii_uppercase)

        self._setup_table()
        self._setup_context_menu()
        self._setup_scroll_connection()

    def _setup_table(self):
        """Configura a tabela principal com tamanhos fixos para as colunas"""
        self.table.setSortingEnabled(True)
        self.table.setCornerButtonEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)

        vertical_header = self.table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(32)
        vertical_header.setMinimumSectionSize(32)
        vertical_header.setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        vertical_header.setFixedWidth(50)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(0, 115)
        header.resizeSection(1, 400)
        header.resizeSection(2, 90)
        header.setSectionsMovable(False)
        header.setHighlightSections(False)
        header.setFixedHeight(32)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStretchLastSection(False)

        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().sectionResized.connect(self._enforce_column_sizes)

    def _enforce_column_sizes(self, logicalIndex, oldSize, newSize):
        header = self.table.horizontalHeader()
        desired_sizes = {0: 115, 1: 400, 2: 90}
        if logicalIndex in desired_sizes and newSize != desired_sizes[logicalIndex]:
            header.blockSignals(True)
            header.resizeSection(logicalIndex, desired_sizes[logicalIndex])
            header.blockSignals(False)

    def _create_row_items(self, sobrenome, nome, rm):
        sobrenome_item = QStandardItem(str(sobrenome))
        nome_item = QStandardItem(str(nome))
        try:
            rm_float = float(rm)
            formatted_rm = "{:,.0f}".format(rm_float).replace(",", ".")
            rm_value = int(rm_float)
        except Exception:
            formatted_rm = str(rm)
            rm_value = rm
        rm_item = QStandardItem(formatted_rm)
        rm_item.setData(rm_value, Qt.UserRole)

        font = QFont()
        font.setBold(True)
        sobrenome_item.setFont(font)
        font_rm = QFont()
        font_rm.setBold(True)
        rm_item.setForeground(QColor(Qt.red))
        rm_item.setFont(font_rm)
        rm_item.setTextAlignment(Qt.AlignCenter)

        return [sobrenome_item, nome_item, rm_item]

    def update_table(self, data=None, sort_column=0, sort_order=Qt.AscendingOrder):
        """Atualiza a tabela com os dados fornecidos ou do excel_manager"""
        if data is None:
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'excel_manager'):
                if hasattr(self.main_window.excel_manager, 'df'):
                    data = self.main_window.excel_manager.df
                else:
                    return
            else:
                return

        if data.empty:
            return

        self.full_data = data.sort_values(
            ['Sobrenome', 'Nome do(a) Aluno(a)'],
            ascending=[True, True]
        ).reset_index(drop=True)
        self.current_chunk = 0
        self.search_active = False

        try:
            self.model.itemChanged.disconnect()
        except Exception:
            pass

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Sobrenome", "Nome do(a) Aluno(a)", "RM"])
        self.proxy_model.setSourceModel(self.model)

        chunk = self.full_data.iloc[:self.CHUNK_SIZE]
        for _, row in chunk.iterrows():
            items = self._create_row_items(row['Sobrenome'], row['Nome do(a) Aluno(a)'], row['RM'])
            self.model.appendRow(items)

        self.current_chunk = 1
        self.table.sortByColumn(sort_column, sort_order)
        self.model.itemChanged.connect(self._on_item_changed)

        # Mostra a página da letra atual
        self.set_page_by_letter(self.current_letter)

    def update_table_with_data(self, data):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Sobrenome", "Nome do(a) Aluno(a)", "RM"])
        for _, row in data.iterrows():
            items = self._create_row_items(row['Sobrenome'], row['Nome do(a) Aluno(a)'], row['RM'])
            self.model.appendRow(items)
        self.proxy_model.setSourceModel(self.model)
        self.search_active = True

    def _load_data_chunk(self):
        if self.is_loading or self.full_data is None or self.full_data.empty:
            return

        self.is_loading = True
        try:
            start = self.current_chunk * self.CHUNK_SIZE
            end = start + self.CHUNK_SIZE
            chunk = self.full_data.iloc[start:end]
            for _, row in chunk.iterrows():
                items = self._create_row_items(row['Sobrenome'], row['Nome do(a) Aluno(a)'], row['RM'])
                self.model.appendRow(items)
            self.current_chunk += 1
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
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.copy_action = QAction("Copiar", self.table)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(self.copy_cell_content)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, position):
        if self.table.selectedIndexes():
            menu = QMenu(self.table)
            menu.addAction(self.copy_action)
            menu.exec_(self.table.viewport().mapToGlobal(position))

    def copy_cell_content(self):
        selected = self.table.selectedIndexes()
        if not selected:
            return False
        clipboard = QApplication.clipboard()
        text = selected[0].data(Qt.DisplayRole)
        clipboard.setText(str(text))
        if self.message_handler:
            self.message_handler.show_temporary_message("Conteúdo copiado!", MESSAGE_SUCCESS)
        return True

    def clear_selection(self):
        self.table.clearSelection()

    def resize_columns(self):
        total_width = self.table.viewport().width()
        rm_width = self.table.columnWidth(2)
        nome_width = max(200, total_width - rm_width)
        self.table.setColumnWidth(0, nome_width)

    def get_selected_rows_data(self):
        """Obtém os dados das linhas selecionadas como uma lista de dicionários"""
        selected_rows = set(index.row() for index in self.table.selectionModel().selectedRows())
        data = []
        for row in selected_rows:
            sobrenome = self.model.item(row, 0).text()
            nome = self.model.item(row, 1).text()
            rm = self.model.item(row, 2).data(Qt.UserRole)
            data.append({'Sobrenome': sobrenome, 'Nome do(a) Aluno(a)': nome, 'RM': rm})
        return data

    def remove_selected_rows(self, excel_manager, data_manager, message_handler):
        selected_data = self.get_selected_rows_data()
        if not selected_data:
            message_handler.show_message("Nenhuma linha selecionada para exclusão", "warning")
            return False
        if not data_manager.remover_alunos(selected_data):
            message_handler.show_message("Erro ao remover alunos", "error")
            return False
        self.update_table(excel_manager.df)
        rows_removed = len(selected_data)
        plural = "s" if rows_removed > 1 else ""
        message_handler.show_message(
            f"{rows_removed} aluno{plural} removido{plural} (clique em Salvar para confirmar)",
            "warning"
        )
        return True

    def _on_item_changed(self, item):
        if not hasattr(self, 'on_edit_callback'):
            return
        proxy_index = item.index()
        if not proxy_index.isValid():
            return
        if proxy_index.model() != self.proxy_model:
            return
        source_index = self.proxy_model.mapToSource(proxy_index)
        if not source_index.isValid():
            return
        row = source_index.row()
        col = source_index.column()
        model = self.proxy_model.sourceModel()
        cell_item = model.item(row, col)
        if cell_item is None:
            return
        value = cell_item.text()
        rm_item = model.item(row, 2)
        if rm_item is None:
            return
        rm = rm_item.data(Qt.UserRole)
        self.on_edit_callback(row, col, value, rm)

    def set_page_by_letter(self, letter):
        """Atualiza a tabela para mostrar apenas alunos cujo sobrenome começa com a letra dada."""
        if not self.full_data is None and not self.full_data.empty:
            self.current_letter = letter.upper()
            mask = self.full_data['Sobrenome'].str.upper().str.startswith(self.current_letter)
            filtered = self.full_data[mask]
            self.update_table_with_data(filtered)
            # Destaca o botão ativo (se MainWindow tiver page_buttons)
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'page_buttons'):
                for l, btn in self.main_window.page_buttons.items():
                    if l == self.current_letter:
                        btn.setProperty("class", "az-page-btn active")
                    else:
                        btn.setProperty("class", "az-page-btn")
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
            if self.message_handler:
                self.message_handler.show_temporary_message(
                    f"Exibindo alunos com sobrenome iniciando por '{self.current_letter}'", "default"
                )

    def next_letter(self):
        idx = self.letters.index(self.current_letter)
        if idx < len(self.letters) - 1:
            self.set_page_by_letter(self.letters[idx + 1])

    def prev_letter(self):
        idx = self.letters.index(self.current_letter)
        if idx > 0:
            self.set_page_by_letter(self.letters[idx - 1])

class NumericSortProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        if left.column() == 2:
            left_data = self.sourceModel().data(left, Qt.UserRole)
            right_data = self.sourceModel().data(right, Qt.UserRole)
            if left_data is not None and right_data is not None:
                return left_data < right_data
        return super().lessThan(left, right)