import logging
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import pandas as pd
from typing import List, Dict, Any

class Command:
    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    def redo(self):
        return self.execute()

class CommandWorker(QObject):
    finished = pyqtSignal(bool, object)

    def __init__(self, command, operation):
        super().__init__()
        self.command = command
        self.operation = operation
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            result = False
            if self.operation == 'execute':
                result = self.command.execute()
            elif self.operation == 'undo':
                result = self.command.undo()
            elif self.operation == 'redo':
                result = self.command.redo()
            self.finished.emit(True, result)
        except Exception as e:
            self.logger.error(f"Erro na operação {self.operation}: {str(e)}")
            self.finished.emit(False, None)

class CommandManager(QObject):
    operation_started = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)

    def __init__(self, max_history=50):
        super().__init__()
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history
        self.logger = logging.getLogger(__name__)
        self.worker_thread = None

    def _run_command_in_thread(self, command, operation, callback):
        self.worker_thread = QThread()
        self.worker = CommandWorker(command, operation)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(callback)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def execute_command(self, command: Command):
        self.operation_started.emit("Processando operação...")
        self._run_command_in_thread(command, 'execute', self._on_command_executed)

    def _on_command_executed(self, success, result):
        if success:
            if len(self.undo_stack) >= self.max_history:
                self.undo_stack.pop(0)
            self.undo_stack.append(self.worker.command)
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
        ).sort_values('RM', ascending=False)
        self.data_manager._build_indexes()
        return True
