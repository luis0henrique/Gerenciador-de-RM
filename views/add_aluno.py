import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QPushButton, QLabel, QMessageBox, QHeaderView,
    QSizePolicy, QWidget, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from utils.ui_helpers import CenterWindowMixin, add_shadow
from utils.styles import get_current_stylesheet

class AddAlunoWindow(QDialog, CenterWindowMixin):
    aluno_adicionado_signal = pyqtSignal()

    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self._init_window_config()
        self.data_manager = data_manager
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
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Central content container
        window_layout = QHBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        main_layout.addLayout(window_layout)

        self.content_widget = QWidget()
        self.content_widget.setMaximumWidth(self.MAX_CONTENT_WIDTH)

        window_layout.addStretch(1)
        window_layout.addWidget(self.content_widget)
        window_layout.addStretch(1)

        # Content layout
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 5, 20, 20)

        # Setup table
        self._setup_table(content_layout)

        # Setup buttons
        self._setup_buttons(content_layout)

    def _setup_table(self, layout):
        """Configure the student input table"""
        self.table = QTableWidget(100, 2)
        self.table.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Table configuration
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.resizeSection(0, 550)
        header.resizeSection(1, 100)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)
        add_shadow(self.table)

        layout.addWidget(QLabel("Preencha os dados dos(as) alunos(as) (Nome|RM):"))
        layout.addWidget(self.table)

    def _setup_buttons(self, layout):
        """Configure the action buttons"""
        btn_layout = QHBoxLayout()

        self.btn_add_alunos = QPushButton("Adicionar Alunos(as)")
        self.btn_cancel = QPushButton("Cancelar")

        # Apply button styling
        self.btn_add_alunos.setProperty("class", "btn_add_alunos")
        self.btn_cancel.setProperty("class", "btn_cancel")
        add_shadow(self.btn_add_alunos, blur=5, x_offset=1, y_offset=1)
        add_shadow(self.btn_cancel, blur=5, x_offset=1, y_offset=1)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_alunos)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def resizeEvent(self, event):
        """Ajusta dinamicamente o layout ao redimensionar"""
        super().resizeEvent(event)
        if hasattr(self, 'content_widget'):
            content_width = min(self.width(), self.MAX_CONTENT_WIDTH)
            self.content_widget.setFixedWidth(content_width)
            if self.content_widget.layout():
                self.content_widget.layout().activate()

    def _connect_signals(self):
        """Conecta os sinais dos botões"""
        self.btn_add_alunos.clicked.connect(self._processar_alunos)
        self.btn_cancel.clicked.connect(self.close)
        self.table.keyPressEvent = self._custom_key_press

    def _custom_key_press(self, event):
        """Handle custom keyboard navigation"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
            self._navegar_para_proxima_celula()
        elif event.key() == Qt.Key_Backtab:
            self._navegar_para_celula_anterior()
        else:
            super().keyPressEvent(event)

    def _navegar_para_proxima_celula(self):
        """Move para a próxima célula ou linha"""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()

        if current_col < self.table.columnCount() - 1:
            self.table.setCurrentCell(current_row, current_col + 1)
        elif current_row < self.table.rowCount() - 1:
            self.table.setCurrentCell(current_row + 1, 0)

    def _navegar_para_celula_anterior(self):
        """Move to previous cell in table"""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()

        if current_col > 0:
            self.table.setCurrentCell(current_row, current_col - 1)
        elif current_row > 0:
            self.table.setCurrentCell(current_row - 1, self.table.columnCount() - 1)

    def _processar_alunos(self):
        """Processa todos os alunos adicionados de forma otimizada"""
        alunos = self._coletar_dados_tabela()
        if not alunos:
            QMessageBox.warning(self, "Aviso", "Nenhum(a) aluno(a) válido(a) para adicionar")
            return

        resultados = self._validar_em_lote(alunos)

        if resultados['problemas_rm']:
            self._mostrar_erros_rm(resultados['problemas_rm'])
            return

        if resultados['rms_duplicados']:
            self._mostrar_rms_duplicados(resultados['rms_duplicados'])
            return

        if resultados['duplicatas'] and not self._mostrar_avisos_similaridade(resultados['duplicatas']):
            return

        if resultados['alunos_validos']:
            self._confirmar_e_adicionar(resultados['alunos_validos'])

    def _coletar_dados_tabela(self):
        """Coleta dados da tabela de forma eficiente"""
        alunos = []
        for row in range(self.table.rowCount()):
            nome_item = self.table.item(row, 0)
            rm_item = self.table.item(row, 1)

            if nome_item and rm_item:
                nome = nome_item.text().strip()
                rm = rm_item.text().strip()
                if nome and rm:
                    alunos.append((row+1, nome, rm))
        return alunos

    def _validar_em_lote(self, alunos):
        """Executa todas as validações em lote"""
        problemas_rm = []
        rms_duplicados = []
        duplicatas = []
        alunos_validos = []
        rms_vistos = set()

        for linha, nome, rm in alunos:
            # RM validation
            if not rm.isdigit():
                problemas_rm.append(f"Linha {linha}: RM '{rm}' não é numérico")
                continue

            rm_int = int(rm)

            # Check for duplicate RMs in current input
            if rm_int in rms_vistos:
                rms_duplicados.append((rm_int, f"Duplicado na linha {linha}"))
                continue
            rms_vistos.add(rm_int)

            # Check for existing RM in database
            if self.data_manager.rm_existe(rm_int):
                aluno_existente = self.data_manager.get_aluno_por_rm(rm_int)
                rms_duplicados.append((rm_int, aluno_existente['Nome do(a) Aluno(a)']))
                continue

            # Check for similar names
            similar_check = self.data_manager.nome_similar_existe(nome)
            if similar_check.get('similar', False):
                duplicatas.append({
                    'linha': linha,
                    'nome_novo': nome,
                    'rm_novo': rm_int,
                    'nome_existente': similar_check['nome_existente'],
                    'rm_existente': similar_check['rm_existente'],
                    'similarity': similar_check['similarity']
                })

            alunos_validos.append((nome, rm_int))

        return {
            'problemas_rm': problemas_rm,
            'rms_duplicados': rms_duplicados,
            'duplicatas': duplicatas,
            'alunos_validos': alunos_validos
        }

    def _mostrar_erros_rm(self, problemas):
        """Mostra erros de RM formatados"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Problemas nos RMs")
        msg.setText("Os seguintes RMs não são numéricos:")
        msg.setDetailedText("\n".join(problemas))
        msg.exec_()

    def _mostrar_rms_duplicados(self, duplicados):
        """Show duplicate RM warnings"""
        dialog = QDialog(self)
        dialog.setWindowTitle("RMs Duplicados")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        message_lines = [
            "<p>Por favor, corrija os <span style='color: #f44336;'><strong>RMs duplicados</strong></span> antes de continuar:</p>",
            "<ul>"
        ]
        message_lines.extend(
            f"<li>RM <b><span style='color: #f44336;'>{rm}</span></b> já existe para: <b><span style='color: #008dce;'>{nome}</span></b></li>"
            for rm, nome in duplicados
        )
        message_lines.append("</ul>")

        text_edit.setHtml("\n".join(message_lines))

        btn_box = QDialogButtonBox()
        btn_ok = btn_box.addButton("OK", QDialogButtonBox.AcceptRole)
        btn_ok.setProperty("class", "btn_add_alunos")
        btn_box.accepted.connect(dialog.accept)

        layout.addWidget(text_edit)
        layout.addWidget(btn_box)
        dialog.exec_()

    def _mostrar_avisos_similaridade(self, duplicatas):
        """Show name similarity warnings"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Aviso de Possíveis Duplicatas")
        dialog.setMinimumSize(700, 500)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        message_lines = ["<p>Possíveis duplicatas encontradas:</p>", "<ul>"]
        for dup in duplicatas:
            message_lines.extend([
                f"<li><b>Linha {dup['linha']}:</b><br>",
                f"• <b>Novo cadastro:</b> {dup['nome_novo']} - RM: {dup['rm_novo']}<br>",
                f"• <b>Aluno(a) existente:</b> {dup['nome_existente']} - RM: {dup['rm_existente']}<br>",
                f"• <b>Similaridade:</b> {dup['similarity']*100:.1f}%</li><br>"
            ])
        message_lines.append("</ul>")
        text_edit.setHtml("\n".join(message_lines))

        btn_box = QDialogButtonBox()
        btn_yes = btn_box.addButton("Continuar mesmo assim", QDialogButtonBox.YesRole)
        btn_no = btn_box.addButton("Corrigir", QDialogButtonBox.NoRole)
        btn_yes.setProperty("class", "btn_add_alunos")
        btn_no.setProperty("class", "btn_cancel")

        btn_yes.clicked.connect(lambda: dialog.done(QMessageBox.Yes))
        btn_no.clicked.connect(lambda: dialog.done(QMessageBox.No))

        layout.addWidget(text_edit)
        layout.addWidget(btn_box)
        return dialog.exec_() == QMessageBox.Yes

    def _confirmar_e_adicionar(self, alunos_validos):
        """Confirma e valida a adição de alunos"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirmar")
        layout = QVBoxLayout(dialog)

        label = QLabel(f"Deseja adicionar {len(alunos_validos)} aluno(a)(s)?")
        layout.addWidget(label)

        btn_box = QDialogButtonBox()
        btn_sim = btn_box.addButton("Sim", QDialogButtonBox.YesRole)
        btn_nao = btn_box.addButton("Não", QDialogButtonBox.NoRole)

        btn_sim.setProperty("class", "btn_add_alunos")
        btn_nao.setProperty("class", "btn_cancel")

        btn_box.accepted.connect(lambda: dialog.done(QMessageBox.Yes))
        btn_box.rejected.connect(lambda: dialog.done(QMessageBox.No))

        layout.addWidget(btn_box)
        btn_nao.setDefault(True)

        if dialog.exec_() == QMessageBox.Yes:
            self._adicionar_alunos(alunos_validos)

    def _adicionar_alunos(self, alunos_validos):
        """Adiciona alunos a database"""
        try:
            novos_dados = pd.DataFrame(
                [(nome, rm) for nome, rm in alunos_validos],
                columns=['Nome do(a) Aluno(a)', 'RM']
            )
            self.data_manager.excel_manager.df = pd.concat(
                [self.data_manager.excel_manager.df, novos_dados],
                ignore_index=True
            ).sort_values('RM')

            QMessageBox.information(
                self,
                "Sucesso",
                f"{len(alunos_validos)} aluno(a)(s) adicionado(a)(s) com sucesso!"
            )
            self.aluno_adicionado_signal.emit()
            self.close()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Falha ao adicionar alunos(as):\n{str(e)}"
            )