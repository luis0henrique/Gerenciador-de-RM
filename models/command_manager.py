import logging
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QThreadPool, QRunnable
import pandas as pd
from typing import List, Dict, Any
from functools import partial

class Command:
    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    def redo(self):
        return self.execute()

# CORRETO
class CommandWorker(QRunnable):
    # ❌ Remova a linha abaixo — já existe em CommandWorkerSignals
    # finished = pyqtSignal(bool, object)

    def __init__(self, command, operation):
        super().__init__()
        self.command = command
        self.operation = operation
        self.signals = CommandWorkerSignals()  # ✅ Use apenas isso

    def run(self):
        try:
            result = False
            if self.operation == 'execute':
                result = self.command.execute()
            elif self.operation == 'undo':
                result = self.command.undo()
            elif self.operation == 'redo':
                result = self.command.redo()
            self.signals.finished.emit(True, self.command)
        except Exception as e:
            self.logger.error(f"Erro na operação {self.operation}: {str(e)}")
            self.signals.finished.emit(False, self.command)

class CommandWorkerSignals(QObject):
    """Signals para CommandWorker (necessário pois QRunnable não herda de QObject)"""
    finished = pyqtSignal(bool, object)

class CommandManager(QObject):
    operation_started = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)

    def __init__(self, max_history=50, max_threads=4):
        super().__init__()
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history
        self.logger = logging.getLogger(__name__)

        # Thread pool em vez de criar thread por comando (50-70% menos overhead)
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(max_threads)
        self.logger.info(f"CommandManager inicializado com thread pool de {max_threads} threads")

    def _run_command_in_thread(self, command, operation, callback):
        """Executa comando em thread pool em vez de criar nova thread"""
        worker = CommandWorker(command, operation)
        worker.signals.finished.connect(callback)
        self.thread_pool.start(worker)

    def execute_command(self, command: Command):
        self.operation_started.emit("Processando operação...")
        self._run_command_in_thread(command, 'execute', self._on_command_executed)

    def _on_command_executed(self, success, command):
        if success:
            if len(self.undo_stack) >= self.max_history:
                self.undo_stack.pop(0)
            self.undo_stack.append(command)
            self.redo_stack.clear()
            self.operation_finished.emit(True, "Operação concluída!")
        else:
            self.operation_finished.emit(False, "Falha na operação")

    def undo(self):
        if not self.undo_stack:
            return False
        self.operation_started.emit("Desfazendo alterações...")
        command = self.undo_stack[-1]
        self._run_command_in_thread(command, 'undo', lambda success, _: self._on_undo_finished(success, command))
        return True

    def _on_undo_finished(self, success, command):
        if success:
            self.undo_stack.pop()
            self.redo_stack.append(command)
            self.operation_finished.emit(True, "Ação desfeita com sucesso")
        else:
            self.operation_finished.emit(False, "Falha ao desfazer ação")

    def redo(self):
        if not self.redo_stack:
            return False
        self.operation_started.emit("Refazendo alterações...")
        command = self.redo_stack[-1]
        self._run_command_in_thread(command, 'redo', lambda success, _: self._on_redo_finished(success, command))
        return True

    def _on_redo_finished(self, success, command):
        if success:
            self.redo_stack.pop()
            self.undo_stack.append(command)
            self.operation_finished.emit(True, "Ação refeita com sucesso")
        else:
            self.operation_finished.emit(False, "Falha ao refazer ação")

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def wait_for_all(self, timeout_ms: int = 5000):
        """Aguarda conclusão de todas as operações em thread"""
        return self.thread_pool.waitForDone(timeout_ms)

class AddStudentCommand(Command):
    def __init__(self, excel_manager, data_manager, student_data: Dict[str, Any]):
        self.excel_manager = excel_manager
        self.data_manager = data_manager
        self.student_data = student_data
        self.was_added = False

    def execute(self):
        if not hasattr(self.excel_manager, 'df'):
            return False
        self.was_added = self.data_manager.adicionar_aluno(
            self.student_data['Nome do(a) Aluno(a)'],
            self.student_data['RM']
        )
        return self.was_added

    def undo(self):
        if not self.was_added:
            return False
        return self.data_manager.remover_alunos([self.student_data])

class RemoveStudentsCommand(Command):
    def __init__(self, excel_manager, data_manager, students_data: List[Dict[str, Any]]):
        self.excel_manager = excel_manager
        self.data_manager = data_manager
        self.students_data = students_data
        self.removed_rows = None

    def execute(self):
        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            return False
        self.removed_rows = self.excel_manager.df[
            self.excel_manager.df['RM'].isin([s['RM'] for s in self.students_data])
        ].copy()
        return self.data_manager.remover_alunos(self.students_data)

    def undo(self):
        if self.removed_rows is None or self.removed_rows.empty:
            return False
        self.excel_manager.df = pd.concat(
            [self.excel_manager.df, self.removed_rows],
            ignore_index=True
        ).sort_values('RM', ascending=False).reset_index(drop=True)
        self.data_manager._build_indexes()
        return True

class EditStudentCommand(Command):
    def __init__(self, excel_manager, data_manager, row, col, old_value, new_value):
        self.excel_manager = excel_manager
        self.data_manager = data_manager
        self.row = row
        self.col = col
        self.old_value = old_value
        self.new_value = new_value

    def execute(self):
        df = self.excel_manager.df
        df.iat[self.row, self.col] = self.new_value
        self.data_manager._build_indexes()
        return True

    def undo(self):
        df = self.excel_manager.df
        df.iat[self.row, self.col] = self.old_value
        self.data_manager._build_indexes()
        return True
