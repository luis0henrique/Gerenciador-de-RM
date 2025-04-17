from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QDesktopWidget, QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer

class CenterWindowMixin:
    def center_window(self):
        """Centraliza a janela na tela"""
        frame_geometry = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

class MessageHandler:
    def __init__(self, parent_widget, layout):
        """
        Inicializa o manipulador de mensagens.

        Args:
            parent_widget: O widget pai que contém o layout
            layout: O layout onde as mensagens serão adicionadas
        """
        self.parent = parent_widget
        self.layout = layout
        self.message_widget = None
        self.current_message = None
        self.default_message = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._show_default_message)

    def init_message_widget(self, position=None):
        """Inicializa o widget de mensagem na posição especificada."""
        if self.message_widget is None:
            self.message_widget = QWidget()
            self.message_widget.setObjectName("messageWidget")
            message_layout = QHBoxLayout(self.message_widget)
            message_layout.setContentsMargins(0, 5, 0, 5)

            # Label único para todas as mensagens
            self.message_label = QLabel()
            self.message_label.setObjectName("messageLabel")
            self.message_label.setProperty("class", "default")  # Classe padrão
            self.message_label.setAlignment(Qt.AlignCenter)
            message_layout.addWidget(self.message_label)  # Corrigido: adiciona o label, não o widget

            # Adiciona ao layout principal
            if position is not None:
                self.layout.insertWidget(position, self.message_widget)
            else:
                self.layout.addWidget(self.message_widget)

    def set_message_type(self, message_type):
        """Define o tipo/classe da mensagem para estilização CSS"""
        if self.message_label:
            self.message_label.setProperty("class", message_type)
            self.message_label.style().unpolish(self.message_label)
            self.message_label.style().polish(self.message_label)

    def set_default_message(self, message_type, text):
        """Define a mensagem padrão que será mostrada quando não houver outras mensagens."""
        self.default_message = (message_type, text)

    def show_message(self, text, message_type="default", timeout=0):
        """
        Exibe uma mensagem temporária.

        Args:
            text: O texto da mensagem
            message_type: Tipo/classe CSS ('default', 'loading', 'search')
            timeout: Tempo para voltar à mensagem padrão (ms)
        """
        if self.message_widget is None:
            self.init_message_widget()

        self.set_message_type(message_type)
        self.message_label.setText(text)
        self.message_widget.setVisible(bool(text))

        if timeout > 0:
            self.timer.start(timeout)

    def show_default_message(self):
        """Mostra a mensagem padrão definida."""
        if self.default_message and self.message_widget:
            message_type, text = self.default_message
            self.message_label.setText(text)
            self.message_widget.setVisible(bool(text))

    def _show_default_message(self):
        """Mostra a mensagem padrão quando o timer expirar."""
        self.timer.stop()
        self.show_default_message()

    def clear_message(self):
        """Limpa a mensagem atual."""
        if self.message_widget:
            self.message_label.setText("")
            self.message_widget.setVisible(False)

def add_shadow(widget, blur=5, x_offset=1, y_offset=1, color=Qt.gray):
    """
    Adiciona efeito de sombra a um widget

    Args:
        widget: O widget que receberá a sombra
        blur: Raio do desfoque da sombra (default: 5)
        x_offset: Deslocamento horizontal (default: 1)
        y_offset: Deslocamento vertical (default: 1)
        color: Cor da sombra (default: Qt.gray)
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)