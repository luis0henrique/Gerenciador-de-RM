import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QPushButton, QLabel, QMessageBox, QHeaderView,
    QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from utils.ui_helpers import CenterWindowMixin, add_shadow
from utils.styles import (get_current_stylesheet)

class AddAlunoWindow(QDialog, CenterWindowMixin):
    aluno_adicionado_signal = pyqtSignal()

    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        # Configurações de janela
        self.setWindowFlags(self.windowFlags() |
                          Qt.WindowMinimizeButtonHint |
                          Qt.WindowMaximizeButtonHint |
                          Qt.WindowSystemMenuHint)

        self.setStyleSheet(get_current_stylesheet())
        self.data_manager = data_manager
        self.setWindowTitle("Adicionar Alunos(as) em Lote")

        # Configurações de tamanho
        self.MINIMUM_WIDTH = 800
        self.MINIMUM_HEIGHT = 600
        self.MAX_CONTENT_WIDTH = 750  # Largura máxima do conteúdo

        self.setMinimumSize(self.MINIMUM_WIDTH, self.MINIMUM_HEIGHT)
        self.resize(self.MAX_CONTENT_WIDTH, 700)  # Tamanho inicial

        # Inicializa a UI antes de centralizar
        self._setup_ui()
        self._connect_signals()

        # Centraliza a janela (agora usando o método do mixin)
        self.center_window()

        # Opcional: Abrir maximizada
        #self.showMaximized()

    def _setup_ui(self):
        """Configura a interface da janela"""
        # Layout principal da janela (vertical)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Layout horizontal para centralizar o conteúdo
        window_layout = QHBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        main_layout.addLayout(window_layout)

        # Container do conteúdo (controla a largura máxima)
        self.content_widget = QWidget()
        self.content_widget.setMaximumWidth(self.MAX_CONTENT_WIDTH)

        # Adiciona espaçadores para centralizar
        window_layout.addStretch(1)
        window_layout.addWidget(self.content_widget)
        window_layout.addStretch(1)

        # Layout vertical principal do conteúdo
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 5, 20, 20)

        # Tabela para entrada em lote (50 linhas)
        self.table = QTableWidget(50, 2)
        self.table.setHorizontalHeaderLabels(["Nome do(a) Aluno(a)", "RM"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Configuração da tabela
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.resizeSection(0, 550)
        header.resizeSection(1, 100)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)

        # Botões
        btn_layout = QHBoxLayout()
        self.btn_add_alunos = QPushButton("Adicionar Alunos(as)")
        self.btn_add_alunos.setProperty("class", "btn_add_alunos")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("class", "btn_cancel")

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_alunos)
        btn_layout.addWidget(self.btn_cancel)

        # Adiciona componentes ao content_layout
        content_layout.addWidget(QLabel("Preencha os dados dos(as) alunos(as) (Nome|RM):"))
        content_layout.addWidget(self.table)
        content_layout.addLayout(btn_layout)

        # Aplica sombras
        add_shadow(self.table)
        add_shadow(self.btn_add_alunos, blur=8, x_offset=2, y_offset=2)
        add_shadow(self.btn_cancel, blur=8, x_offset=2, y_offset=2)

    def resizeEvent(self, event):
        """Ajusta dinamicamente o layout ao redimensionar"""
        super().resizeEvent(event)

        if hasattr(self, 'content_widget'):
            # Calcula a largura efetiva do conteúdo
            content_width = min(self.width(), self.MAX_CONTENT_WIDTH)

            # Ajusta a largura do content_widget
            self.content_widget.setFixedWidth(content_width)

            # Força atualização do layout
            if self.content_widget.layout():
                self.content_widget.layout().activate()

    def _connect_signals(self):
        """Conecta os sinais dos botões"""
        self.btn_add_alunos.clicked.connect(self._processar_alunos)
        self.btn_cancel.clicked.connect(self.close)

        # Configura navegação por teclado
        self.table.keyPressEvent = self._custom_key_press

    def _custom_key_press(self, event):
        """Navegação personalizada por teclado"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._navegar_para_proxima_celula()
        elif event.key() == Qt.Key_Tab:
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
        """Move para a célula anterior"""
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

        # Pré-processamento em lote
        resultados = self._validar_em_lote(alunos)

        # Exibe erros se houver
        if resultados['problemas_rm']:
            self._mostrar_erros_rm(resultados['problemas_rm'])
            return

        if resultados['rms_duplicados']:
            self._mostrar_rms_duplicados(resultados['rms_duplicados'])
            return

        # Mostra aviso de nomes similares
        if resultados['duplicatas']:
            if not self._mostrar_avisos_similaridade(resultados['duplicatas']):
                return

        # Confirmação final e adição
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

        # Primeira passada: valida RMs
        alunos_para_verificar_nome = []
        rms_vistos = set()

        for linha, nome, rm in alunos:
            # Validação do RM
            if not rm.isdigit():
                problemas_rm.append(f"Linha {linha}: RM '{rm}' não é numérico")
                continue

            rm_int = int(rm)

            # Verifica RM duplicado na própria entrada
            if rm_int in rms_vistos:
                rms_duplicados.append((rm_int, f"Duplicado na linha {linha}"))
                continue
            rms_vistos.add(rm_int)

            # Verifica RM duplicado no banco de dados
            if self.data_manager.rm_existe(rm_int):
                aluno_existente = self.data_manager.get_aluno_por_rm(rm_int)
                rms_duplicados.append((rm_int, aluno_existente['Nome do(a) Aluno(a)']))
                continue

            alunos_para_verificar_nome.append((linha, nome, rm_int))

        # Segunda passada: verifica similaridade de nomes (apenas para alunos com RM válido)
        for linha, nome, rm in alunos_para_verificar_nome:
            similar_check = self.data_manager.nome_similar_existe(nome)
            if similar_check['similar']:
                duplicatas.append({
                    'linha': linha,
                    'nome_novo': nome,
                    'rm_novo': rm,
                    'nome_existente': similar_check['nome_existente'],
                    'rm_existente': similar_check['rm_existente'],
                    'similarity': similar_check['similarity']
                })
            alunos_validos.append((nome, rm))

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
        """Mostra RMs duplicados formatados"""
        mensagem = """
        <p>Por favor, <span style="color: red;">corrija os RMs duplicados</span> antes de continuar:</p>
        <ul>"""

        for rm, nome in duplicados:
            mensagem += f"""
            <li>RM <b>{rm}</b> já existe para: <b>{nome}</b></li>
            """

        mensagem += "</ul>"

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("RMs Duplicados")
        msg.setTextFormat(Qt.RichText)
        msg.setText(mensagem)
        msg.exec_()

    def _mostrar_avisos_similaridade(self, duplicatas):
        """Mostra avisos de similaridade e retorna se deve continuar"""
        mensagem = """
        <p><b>Possíveis duplicatas encontradas:</b></p>
        <ul>"""

        for dup in duplicatas:
            mensagem += f"""
            <li>
                <b>Linha {dup['linha']}:</b><br>
                • <b>Novo cadastro:</b> {dup['nome_novo']} (RM: <b>{dup['rm_novo']}</b>)<br>
                • <b>Aluno(a) existente:</b> {dup['nome_existente']} (RM: <b>{dup['rm_existente']}</b>)<br>
                • <b>Similaridade:</b> {dup['similarity']*100:.1f}%
            </li>
            <br>
            """

        mensagem += "</ul>"

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Aviso de Possíveis Duplicatas")
        msg.setTextFormat(Qt.RichText)
        msg.setText(mensagem)
        msg.setStyleSheet("QLabel{min-width: 600px;}")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText("Continuar mesmo assim")
        msg.button(QMessageBox.No).setText("Corrigir")

        return msg.exec_() == QMessageBox.Yes

    def _confirmar_e_adicionar(self, alunos_validos):
        """Confirma e adiciona alunos válidos"""
        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"Deseja adicionar {len(alunos_validos)} aluno(a)(s)?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                # Adiciona em lote
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
                    f"{len(alunos_validos)} aluno(a)(s) adicionado(s) com sucesso!"
                )
                self.aluno_adicionado_signal.emit()
                self.close()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Falha ao adicionar alunos(as):\n{str(e)}"
                )