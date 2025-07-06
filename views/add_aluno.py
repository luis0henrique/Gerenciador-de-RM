from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QPushButton, QLabel, QMessageBox, QHeaderView,
    QSizePolicy, QWidget, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from utils.ui_helpers import CenterWindowMixin, add_shadow, update_shadows_on_theme_change, TableNavigationMixin, CornerSquare
from utils.helpers import formatar_nome
from utils.styles import get_current_stylesheet
from views.components.dialogs import AlunoDialogs
from models.command_manager import AddStudentCommand

class CustomMessageBox(QMessageBox):
    """QMessageBox customizado para ignorar Enter/Return no fechamento."""
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        else:
            super().keyPressEvent(event)

class AddAlunoWindow(QDialog, CenterWindowMixin, TableNavigationMixin):
    aluno_adicionado_signal = pyqtSignal()

    def __init__(self, parent=None, data_manager=None, excel_manager=None, command_manager=None):
        super().__init__(parent)
        self.setProperty("class", "MainBackgroundWindow")
        self._init_window_config()
        self.data_manager = data_manager
        self.excel_manager = excel_manager
        self.command_manager = command_manager
        self._init_ui()
        self._connect_signals()
        self.center_window()

    def _init_window_config(self):
        """Inicia a configuração da janela"""
        self.setWindowFlags(self.windowFlags() |
                          Qt.WindowMinimizeButtonHint |
                          Qt.WindowMaximizeButtonHint |
                          Qt.WindowSystemMenuHint)

        self.setStyleSheet(get_current_stylesheet())
        self.setWindowTitle("Adicionar Alunos(as) em Lote")

        # Window size settings
        self.MINIMUM_WIDTH = 800
        self.MINIMUM_HEIGHT = 600
        self.MAX_CONTENT_WIDTH = 750

        self.setMinimumSize(self.MINIMUM_WIDTH, self.MINIMUM_HEIGHT)
        self.resize(self.MAX_CONTENT_WIDTH, 700)

    def _init_ui(self):
        """Inicia a interface da janela"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        window_layout = QHBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        main_layout.addLayout(window_layout)

        self.content_widget = QWidget()
        self.content_widget.setMaximumWidth(self.MAX_CONTENT_WIDTH)

        window_layout.addStretch(1)
        window_layout.addWidget(self.content_widget)
        window_layout.addStretch(1)

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 5, 20, 20)

        self._setup_table(content_layout)
        self._setup_buttons(content_layout)
        self._setup_rm_validation()

    def _setup_table(self, layout):
        """Configura a tabela de entrada do aluno"""
        self.table = QTableWidget(100, 2)  # 100 linhas, 2 colunas
        self.table.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])
        self.table.setToolTip(
            "Digite os nomes dos alunos na primeira coluna e os RMs na segunda\n"
            "Use Enter / Tab / Shift+Tab para navegar entre células\n"
        )
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setCornerButtonEnabled(False)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)

        vertical_header = self.table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(32)
        vertical_header.setMinimumSectionSize(32)
        vertical_header.setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        vertical_header.setFixedWidth(50)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(0, 550)
        header.resizeSection(1, 100)
        header.setFixedHeight(32)

        self.corner_square = CornerSquare(self.table)
        self.corner_square.move(1, 1)
        self.corner_square.raise_()

        add_shadow(self.table)

        layout.addWidget(QLabel("Preencha os dados dos(as) alunos(as) (Nome|RM):"))
        layout.addWidget(self.table)

    def update_ui_on_theme_change(self):
        """Atualiza elementos da UI quando o tema muda."""
        elements_with_shadow = [
            self.table,
            self.btn_add_alunos,
            self.btn_cancel
        ]
        update_shadows_on_theme_change(elements_with_shadow)

    def _setup_buttons(self, layout):
        """Configura os botões de ação"""
        btn_layout = QHBoxLayout()

        self.btn_add_alunos = QPushButton("Adicionar Alunos(as)")
        self.btn_add_alunos.setToolTip("Valida e adiciona os alunos ao arquivo")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setToolTip("Fecha esta janela sem adicionar alunos")

        self.btn_add_alunos.setProperty("class", "btn_add_alunos")
        self.btn_cancel.setProperty("class", "btn_cancel")

        add_shadow(self.btn_add_alunos)
        add_shadow(self.btn_cancel)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_alunos)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def resizeEvent(self, event):
        """Ajusta dinamicamente o layout e a posição do quadrado ao redimensionar"""
        super().resizeEvent(event)
        if hasattr(self, 'content_widget'):
            content_width = min(self.width(), self.MAX_CONTENT_WIDTH)
            self.content_widget.setFixedWidth(content_width)
            if self.content_widget.layout():
                self.content_widget.layout().activate()
        if hasattr(self, 'corner_square'):
            self.corner_square.move(1, 1)

    def _connect_signals(self):
        """Conecta os sinais dos botões"""
        self.btn_add_alunos.clicked.connect(self._processar_alunos)
        self.btn_cancel.clicked.connect(self.close)
        self.table.keyPressEvent = lambda event: self.handle_table_key_press(event, self.table)

    def _coletar_dados_tabela(self):
        """Coleta dados da tabela de forma eficiente"""
        alunos = []
        for row in range(self.table.rowCount()):
            nome_item = self.table.item(row, 0)
            rm_item = self.table.item(row, 1)
            nome = formatar_nome(nome_item.text().strip()) if nome_item and nome_item.text().strip() else ""
            rm = rm_item.text().strip() if rm_item and rm_item.text().strip() else ""
            if nome and rm:
                alunos.append((row+1, nome, rm))
        return alunos

    def _processar_alunos(self):
        """Processa todos os alunos adicionados de forma otimizada"""
        alunos = self._coletar_dados_tabela()
        if not alunos:
            self._safe_show_message("Aviso", "Nenhum(a) aluno(a) válido(a) para adicionar", QMessageBox.Warning)
            return

        resultados = self.data_manager.validar_alunos_em_lote(alunos)

        if resultados['duplicatas'] and not AlunoDialogs.show_similarity_warnings(self, resultados['duplicatas']):
            return

        if resultados['alunos_validos'] and AlunoDialogs.show_confirmation_dialog(self, resultados['alunos_validos']):
            self._adicionar_alunos(resultados['alunos_validos'])

    def _adicionar_alunos(self, alunos_validos):
        """Adiciona alunos ao banco de dados de forma síncrona"""
        try:
            self.btn_add_alunos.setEnabled(False)
            self.btn_add_alunos.setText("Adicionando...")

            for nome, rm in alunos_validos:
                self.data_manager.adicionar_aluno(nome, int(rm))
                QApplication.processEvents()

            self._safe_show_message(
                "Sucesso",
                f"{len(alunos_validos)} aluno(s) adicionado(s) com sucesso!",
                QMessageBox.Information
            )

            self.aluno_adicionado_signal.emit()
            self.close()

        except Exception as e:
            self._safe_show_message(
                "Erro",
                f"Falha ao adicionar aluno(s):\n{str(e)}",
                QMessageBox.Critical
            )
        finally:
            self.btn_add_alunos.setEnabled(True)
            self.btn_add_alunos.setText("Adicionar Alunos(as)")

    def _setup_rm_validation(self):
        """Configura a validação de RM em tempo real"""
        self.table.itemChanged.connect(self._schedule_rm_validation)

    def _schedule_rm_validation(self, item):
        """Agenda a validação para evitar problemas de thread"""
        if item.column() == 1:  # Só validamos a coluna de RM
            QTimer.singleShot(0, lambda: self._validate_rm_on_edit(item))

    def _validate_rm_on_edit(self, item):
        """Valida o RM quando uma célula é editada"""
        try:
            if not item or item.column() != 1:
                return

            rm = item.text().strip()
            if not rm:
                return

            # Verifica se é número válido
            try:
                rm_int = int(rm)
            except ValueError:
                self._show_invalid_rm_message(item)
                return

            # Verifica duplicatas na tabela
            duplicates_in_table = self._check_duplicates_in_table(rm_int, item.row())
            if duplicates_in_table:
                self._show_duplicate_message(rm_int, duplicates_in_table, item)
                return

            # Verifica duplicatas no arquivo
            if self.data_manager and hasattr(self.data_manager, 'excel_manager'):
                df = self.data_manager.excel_manager.df
                if not df.empty and rm_int in df['RM'].values:
                    aluno_existente = df[df['RM'] == rm_int].iloc[0]['Nome do(a) Aluno(a)']
                    self._show_duplicate_message(rm_int, [aluno_existente], item)
                    return

        except Exception as e:
            print(f"Erro durante validação: {str(e)}")

    def _check_duplicates_in_table(self, rm, current_row):
        """Verifica se o RM já existe em outras linhas da tabela"""
        duplicates = []
        for row in range(self.table.rowCount()):
            if row == current_row:
                continue
            rm_item = self.table.item(row, 1)
            if rm_item and rm_item.text().strip():
                try:
                    if int(rm_item.text().strip()) == rm:
                        nome_item = self.table.item(row, 0)
                        nome = nome_item.text().strip() if nome_item and nome_item.text().strip() else "Sem nome"
                        duplicates.append(nome)
                except ValueError:
                    continue
        return duplicates

    def _show_invalid_rm_message(self, item):
        """Mostra mensagem de RM inválido e seleciona a célula para correção"""
        QTimer.singleShot(0, lambda: (
            self._safe_show_message(
                "RM Inválido",
                "A coluna RM deve conter apenas números inteiros.\n",
                QMessageBox.Warning
            ),
            self._select_item(item)
        ))

    def _show_duplicate_message(self, rm, duplicates, item):
        """Mostra mensagem de RM duplicado e seleciona a célula para correção"""
        if len(duplicates) == 1:
            msg = f"O RM {rm} já está sendo usado por:\n{duplicates[0]}"
        else:
            msg = f"O RM {rm} está duplicado na tabela para:\n" + "\n".join(duplicates)

        QTimer.singleShot(0, lambda: (
            self._safe_show_message(
                "RM Duplicado",
                f"{msg}\n\nPor favor, corrija o RM antes de continuar.",
                QMessageBox.Warning
            ),
            self._select_item(item)
        ))

    def _select_item(self, item):
        """Seleciona a célula para facilitar a correção pelo usuário"""
        self.table.setCurrentItem(item)
        self.table.editItem(item)

    def _safe_show_message(self, title, message, icon):
        """Mostra a mensagem de forma segura na thread principal"""
        msg_box = CustomMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()