from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QPushButton, QMessageBox, QWidget, QApplication, QSizePolicy,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from utils.ui_helpers import CenterWindowMixin, add_shadow, update_shadows_on_theme_change, CornerSquare
from utils.helpers import formatar_nome, extrair_sobrenome
from utils.styles import get_current_stylesheet
from models.command_manager import EditStudentCommand

class EditAlunoWindow(QDialog, CenterWindowMixin):
    """Janela para editar informações de um aluno individual"""
    aluno_editado_signal = pyqtSignal()

    def __init__(self, parent=None, data_manager=None, excel_manager=None, command_manager=None, aluno_data=None):
        super().__init__(parent)
        self.setProperty("class", "MainBackgroundWindow")
        self.data_manager = data_manager
        self.excel_manager = excel_manager
        self.command_manager = command_manager
        self.aluno_data = aluno_data or {}

        self._init_window_config()
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
        self.setWindowTitle("Editar Aluno(a)")

        self.setMinimumWidth(500)
        self.setMinimumHeight(200)
        self.resize(500, 220)

    def _init_ui(self):
        """Inicia a interface da janela"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        title_label = QLabel("Editar Informações do Aluno(a)")
        title_font = title_label.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Formulário: tabela de 1 linha com 2 colunas (Nome, RM)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(5)  # reduce vertical gap between table and buttons

        self.table = QTableWidget(1, 2)
        self.table.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])
        nome_atual = self.aluno_data.get('Nome do(a) Aluno(a)', '')
        rm_value = self.aluno_data.get('RM', '')
        item_nome = QTableWidgetItem(str(nome_atual))
        item_rm = QTableWidgetItem(str(int(rm_value)) if rm_value not in (None, '') else "")
        self.table.setItem(0, 0, item_nome)
        self.table.setItem(0, 1, item_rm)

        # Apply same visual/setup rules as AddAlunoWindow for consistency
        self.table.setToolTip(
            "Digite o nome do aluno na primeira coluna e o RM na segunda\n"
            "Use Enter / Tab para navegar entre células"
        )
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.table.setCornerButtonEnabled(False)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)

        vertical_header = self.table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(40)
        vertical_header.setMinimumSectionSize(32)
        vertical_header.setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        vertical_header.setFixedWidth(50)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 120)
        header.setFixedHeight(32)

        # corner square similar to add_aluno table
        self.corner_square = CornerSquare(self.table)
        self.corner_square.move(1, 1)
        self.corner_square.raise_()

        # Make the table height just enough to show header + one row
        row_height = vertical_header.defaultSectionSize()
        total_height = header.height() + row_height + 20
        self.table.setFixedHeight(total_height)

        add_shadow(self.table)

        form_layout.addWidget(self.table)
        main_layout.addLayout(form_layout)
        # remove large stretch to keep buttons closer
        # main_layout.addStretch()

        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_salvar = QPushButton("Salvar Alterações")
        self.btn_salvar.setToolTip("Salva as alterações do aluno")
        self.btn_salvar.setProperty("class", "btn_add_alunos")
        self.btn_salvar.setMinimumWidth(150)
        add_shadow(self.btn_salvar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setToolTip("Fecha sem salvar")
        self.btn_cancelar.setProperty("class", "btn_cancel")
        self.btn_cancelar.setMinimumWidth(150)
        add_shadow(self.btn_cancelar)

        btn_layout.addWidget(self.btn_salvar)
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'corner_square'):
            self.corner_square.move(1, 1)

    def update_ui_on_theme_change(self):
        """Atualiza elementos da UI quando o tema muda"""
        elements_with_shadow = [
            self.table,
            self.btn_salvar,
            self.btn_cancelar
        ]
        update_shadows_on_theme_change(elements_with_shadow)

    def _connect_signals(self):
        """Conecta os sinais dos botões"""
        self.btn_salvar.clicked.connect(self._salvar_alteracoes)
        self.btn_cancelar.clicked.connect(self.reject)

    def _salvar_alteracoes(self):
        """Valida e salva as alterações do aluno"""
        # Coleta valores da tabela (linha 0)
        item_nome = self.table.item(0, 0)
        item_rm = self.table.item(0, 1)
        nome = (item_nome.text().strip() if item_nome else '').strip()
        rm_str = (item_rm.text().strip() if item_rm else '').strip()

        if not nome:
            QMessageBox.warning(self, "Erro", "O nome não pode estar vazio.")
            return

        if not rm_str:
            QMessageBox.warning(self, "Erro", "O RM não pode estar vazio.")
            return

        try:
            novo_rm = int(rm_str)
        except ValueError:
            QMessageBox.warning(self, "Erro", "O RM deve conter apenas números.")
            return

        # Localiza aluno original pelo RM antigo
        rm_antigo = self.aluno_data.get('RM')
        try:
            rm_antigo_int = int(rm_antigo) if rm_antigo not in (None, '') else None
        except Exception:
            rm_antigo_int = None

        df = self.excel_manager.df
        # Verifica existência de RM duplicado (exceto o próprio registro)
        if rm_antigo_int is None:
            match = df[df['RM'] == novo_rm]
        else:
            if novo_rm != rm_antigo_int and novo_rm in df['RM'].values:
                aluno_existente = df[df['RM'] == novo_rm].iloc[0]['Nome do(a) Aluno(a)']
                QMessageBox.warning(
                    self,
                    "RM Duplicado",
                    f"Já existe um aluno com o RM {novo_rm}:\n{aluno_existente}\n\nPor favor, verifique o RM."
                )
                return
            match = df[df['RM'] == rm_antigo_int]

        if match.empty:
            QMessageBox.warning(self, "Erro", "Aluno não encontrado na base de dados.")
            self.reject()
            return

        real_idx = match.index[0]

        # Formata nome e extrai sobrenome (mesma lógica do adicionar)
        nome_formatado = formatar_nome(nome)
        sobrenome_novo = extrair_sobrenome(nome_formatado)

        # Checa nomes similares (usar índice do data_manager)
        try:
            similar = self.data_manager.nome_similar_existe(nome_formatado)
            if similar.get('similar', False):
                rm_existente = similar.get('rm_existente')
                # ignora se o resultado for o próprio registro (rm antigo)
                if rm_existente != rm_antigo_int:
                    # pergunta se deseja continuar apesar do nome semelhante
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Nome Similar")
                    msg.setText(
                        f"Nome semelhante encontrado: {similar.get('nome_existente')} (RM: {rm_existente}).\n"
                        "Deseja continuar mesmo assim?"
                    )
                    btn_continue = msg.addButton("Continuar", QMessageBox.YesRole)
                    btn_cancel = msg.addButton("Cancelar", QMessageBox.NoRole)
                    msg.setDefaultButton(btn_cancel)
                    msg.exec_()
                    if msg.clickedButton() is btn_cancel:
                        return
        except Exception:
            # Se não houver data_manager ou erro, segue em frente
            pass

        # Prepara e executa comandos de edição para cada coluna alterada
        try:
            old_sobrenome = df.iat[real_idx, 0]
            old_nome = df.iat[real_idx, 1]
            old_rm = df.iat[real_idx, 2]

            edits = []
            if str(sobrenome_novo) != str(old_sobrenome):
                edits.append((0, sobrenome_novo, old_sobrenome))
            if str(nome_formatado) != str(old_nome):
                edits.append((1, nome_formatado, old_nome))
            if int(novo_rm) != int(old_rm):
                edits.append((2, int(novo_rm), old_rm))

            for col, new_val, old_val in edits:
                edit_command = EditStudentCommand(
                    self.excel_manager,
                    self.data_manager,
                    real_idx,
                    col,
                    old_val,
                    new_val
                )
                self.command_manager.execute_command(edit_command)

            self.aluno_editado_signal.emit()
            QMessageBox.information(self, "Sucesso", "Aluno editado com sucesso!\n(Clique em Salvar para confirmar as alterações)")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar aluno: {str(e)}")
