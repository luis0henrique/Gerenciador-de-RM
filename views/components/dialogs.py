from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel

class AlunoDialogs:
    @staticmethod
    def show_rm_errors(parent, problemas):
        """Exibe uma mensagem de erro para RMs não numéricos."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Problemas nos RMs")
        msg.setText("Os seguintes RMs não são numéricos:")
        msg.setDetailedText("\n".join(problemas))
        msg.exec_()

    @staticmethod
    def show_duplicate_rms(parent, duplicados):
        """Exibe aviso de RMs duplicados."""
        dialog = QDialog(parent)
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

    @staticmethod
    def show_similarity_warnings(parent, duplicatas):
        """Exibe aviso de possíveis duplicatas por similaridade de nome."""
        dialog = QDialog(parent)
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

    @staticmethod
    def show_confirmation_dialog(parent, alunos_validos):
        """Exibe diálogo de confirmação para adicionar alunos."""
        dialog = QDialog(parent)
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

        return dialog.exec_() == QMessageBox.Yes

    @staticmethod
    def show_import_duplicate_rms(parent, rms_duplicados):
        """Exibe aviso de RMs duplicados encontrados na importação."""
        dialog = QDialog(parent)
        dialog.setWindowTitle("RMs Duplicados na Importação")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        message_lines = [
            "<p><strong>Os seguintes RMs já existem na base de dados e não serão importados:</strong></p>",
            "<ul style='list-style-type: none; padding-left: 10px;'>"
        ]
        message_lines.extend(
            f"<li>RM <span style='color: #f44336; font-weight: bold;'>{rm}</span> - {nome}</li>"
            for rm, nome in rms_duplicados
        )
        message_lines.append("</ul>")
        message_lines.append(
            "<p style='margin-top: 15px;'><em>Clique em 'OK' para continuar com a importação dos demais alunos.</em></p>"
        )

        text_edit.setHtml("\n".join(message_lines))

        btn_box = QDialogButtonBox()
        btn_ok = btn_box.addButton("OK", QDialogButtonBox.AcceptRole)
        btn_ok.setProperty("class", "btn_add_alunos")
        btn_box.accepted.connect(dialog.accept)

        layout.addWidget(text_edit)
        layout.addWidget(btn_box)
        dialog.exec_()

    @staticmethod
    def show_import_confirmation_dialog(parent, total_importados, total_validos, rms_duplicados_count=0):
        """Exibe diálogo de confirmação para importação de alunos."""
        dialog = QDialog(parent)
        dialog.setWindowTitle("Confirmar Importação")
        dialog.setMinimumSize(500, 200)
        layout = QVBoxLayout(dialog)

        message_parts = [f"<b>Resumo da Importação:</b><br><br>"]
        message_parts.append(f"• Total de registros no arquivo: <b>{total_importados}</b><br>")
        message_parts.append(f"• Alunos válidos a importar: <b style='color: #4caf50;'>{total_validos}</b><br>")

        if rms_duplicados_count > 0:
            message_parts.append(f"• RMs duplicados (não importarão): <b style='color: #f44336;'>{rms_duplicados_count}</b><br>")

        message_parts.append("<br><b>Deseja continuar com a importação?</b>")

        label = QLabel("\n".join(message_parts))
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        btn_box = QDialogButtonBox()
        btn_sim = btn_box.addButton("Sim, Importar", QDialogButtonBox.YesRole)
        btn_nao = btn_box.addButton("Cancelar", QDialogButtonBox.NoRole)

        btn_sim.setProperty("class", "btn_add_alunos")
        btn_nao.setProperty("class", "btn_cancel")

        btn_box.accepted.connect(lambda: dialog.done(QMessageBox.Yes))
        btn_box.rejected.connect(lambda: dialog.done(QMessageBox.No))

        layout.addWidget(btn_box)
        btn_nao.setDefault(True)

        return dialog.exec_() == QMessageBox.Yes