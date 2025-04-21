import logging
from PyQt5.QtCore import Qt
from utils.helpers import remove_acentos

class SearchManager:
    def __init__(self, excel_manager, table_manager, message_handler):
        self.logger = logging.getLogger(__name__)
        self.excel_manager = excel_manager
        self.table_manager = table_manager
        self.message_handler = message_handler

    def search_student(self, search_term):
        """Executa a busca por aluno baseada no termo fornecido"""
        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            return False

        if not search_term.strip():
            self.restore_full_list()
            return True

        normalized_term = remove_acentos(search_term.lower())

        if normalized_term.isdigit():
            result = self.excel_manager.df[self.excel_manager.df['RM'].astype(str) == normalized_term]
            self.message_handler.show_search_results(len(result), by_rm=True)
        else:
            mask = self.excel_manager.df['Nome do(a) Aluno(a)'].apply(
                lambda x: normalized_term in remove_acentos(str(x).lower()))
            result = self.excel_manager.df[mask]
            self.message_handler.show_search_results(len(result), by_rm=False)

        result_sorted = result.sort_values('Nome do(a) Aluno(a)')
        self.table_manager.update_table_with_data(result_sorted)
        self.table_manager.table.sortByColumn(0, Qt.AscendingOrder)
        return True

    def restore_full_list(self):
        """Restaura a lista completa de alunos"""
        if hasattr(self.excel_manager, 'df'):
            record_count = len(self.excel_manager.df)
            self.message_handler.show_record_count(record_count)
            self.table_manager.update_table()
        return True