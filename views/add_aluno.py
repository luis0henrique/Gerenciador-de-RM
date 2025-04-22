import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QPushButton, QLabel, QMessageBox, QHeaderView,
    QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from utils.ui_helpers import CenterWindowMixin, add_shadow, update_shadows_on_theme_change, TableNavigationMixin, CornerSquare
from utils.helpers import formatar_nome
from utils.styles import get_current_stylesheet
from views.components.dialogs import AlunoDialogs

class AddAlunoWindow(QDialog, CenterWindowMixin, TableNavigationMixin):
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
        """Configura a tabela de entrada do aluno"""
        # Criação inicial da tabela
        self.table = QTableWidget(100, 2) # 100 linhas, 2 colunas
        self.table.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])
        self.table.setToolTip(
            "Digite os nomes dos alunos na primeira coluna e os RMs na segunda\n"
            "Use Enter / Tab / Shift+Tab para navegar entre células\n"
        )
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setCornerButtonEnabled(False)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers) # Permite editar todas as células

        # Cabeçalho vertical (índices)
        vertical_header = self.table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed) # Fixa o tamanho
        vertical_header.setDefaultSectionSize(32) # Altura padrão das linhas
        vertical_header.setMinimumSectionSize(32) # Tamanho mínimo
        vertical_header.setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        vertical_header.setFixedWidth(50) # Largura fixa para a coluna de índices

        # Cabeçalho horizontal (colunas)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch) # Coluna de nomes
        header.setSectionResizeMode(1, QHeaderView.Fixed) #Coluna de RM
        header.resizeSection(0, 550) #Largura inicial coluna de nomes
        header.resizeSection(1, 100) # Largura fixa para coluna de RM
        header.setFixedHeight(32) # Altura fixa para o header horizontal

        # Cria e posiciona o quadrado manualmente
        self.corner_square = CornerSquare(self.table)
        self.corner_square.move(1, 1) # Posiciona no canto superior esquerdo
        self.corner_square.raise_() # Garante que fique acima dos headers

        # Aplica sombra dinâmica
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
        """Configure the action buttons"""
        btn_layout = QHBoxLayout()

        self.btn_add_alunos = QPushButton("Adicionar Alunos(as)")
        self.btn_add_alunos.setToolTip("Valida e adiciona os alunos ao arquivo")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setToolTip("Fecha esta janela sem adicionar alunos")

        # Apply button styling
        self.btn_add_alunos.setProperty("class", "btn_add_alunos")
        self.btn_cancel.setProperty("class", "btn_cancel")

        # Aplica sombras dinâmicas
        add_shadow(self.btn_add_alunos)
        add_shadow(self.btn_cancel)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_alunos)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def resizeEvent(self, event):
        """Ajusta dinamicamente o layout e a posição do quadrado ao redimensionar"""
        super().resizeEvent(event)

        # Ajusta dinamicamente o layout ao redimensionar
        if hasattr(self, 'content_widget'):
            content_width = min(self.width(), self.MAX_CONTENT_WIDTH)
            self.content_widget.setFixedWidth(content_width)
            if self.content_widget.layout():
                self.content_widget.layout().activate()

        # Ajusta a posição do quadrado quando a tabela é redimensionada
        if hasattr(self, 'corner_square'):
            self.corner_square.move(1, 1)

    def _connect_signals(self):
        """Conecta os sinais dos botões"""
        self.btn_add_alunos.clicked.connect(self._processar_alunos)
        self.btn_cancel.clicked.connect(self.close)
        self.table.keyPressEvent = lambda event: self.handle_table_key_press(event, self.table)

    def _processar_alunos(self):
        """Processa todos os alunos adicionados de forma otimizada"""
        alunos = self._coletar_dados_tabela()
        if not alunos:
            QMessageBox.warning(self, "Aviso", "Nenhum(a) aluno(a) válido(a) para adicionar")
            return

        resultados = self.data_manager.validar_alunos_em_lote(alunos)

        if resultados['problemas_rm']:
            AlunoDialogs.show_rm_errors(self, resultados['problemas_rm'])
            return

        if resultados['rms_duplicados']:
            AlunoDialogs.show_duplicate_rms(self, resultados['rms_duplicados'])
            return

        if resultados['duplicatas'] and not AlunoDialogs.show_similarity_warnings(self, resultados['duplicatas']):
            return

        if resultados['alunos_validos'] and AlunoDialogs.show_confirmation_dialog(self, resultados['alunos_validos']):
            self._adicionar_alunos(resultados['alunos_validos'])

    def _coletar_dados_tabela(self):
        """Coleta dados da tabela de forma eficiente"""
        alunos = []
        for row in range(self.table.rowCount()):
            nome_item = self.table.item(row, 0)
            rm_item = self.table.item(row, 1)
            if nome_item and rm_item:
                nome = formatar_nome(nome_item.text().strip())  # Formata aqui
                rm = rm_item.text().strip()
                if nome and rm:
                    alunos.append((row+1, nome, rm))
        return alunos

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