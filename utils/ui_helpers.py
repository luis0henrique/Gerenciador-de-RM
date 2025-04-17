from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QDesktopWidget, QLabel, QHBoxLayout, QWidget
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
        self.message_label = None
        self.default_message = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._restore_default)

    def init_message_widget(self, position=None):
        """Inicializa o widget de mensagem na posição especificada."""
        if self.message_widget is None:
            self.message_widget = QWidget()
            self.message_widget.setObjectName("messageWidget")
            layout = QHBoxLayout(self.message_widget)
            layout.setContentsMargins(0, 5, 0, 5)

            # Label único para todas as mensagens
            self.message_label = QLabel()
            self.message_label.setObjectName("messageLabel")
            self.message_label.setProperty("class", "default")
            self.message_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.message_label)

            # Adiciona ao layout principal
            if position is not None:
                self.layout.insertWidget(position, self.message_widget)
            else:
                self.layout.addWidget(self.message_widget)

            # Mostra o widget imediatamente (mesmo vazio)
            self.message_widget.setVisible(True)

    def set_default_message(self, text, message_type="default"):
        """Define a mensagem padrão que será mostrada quando não houver outras"""
        self.default_message = (text, message_type)
        self._show_default()  # Mostra imediatamente

    def show_message(self, text, message_type="default", timeout=0):
        """Mostra uma mensagem temporária"""
        if self.message_widget is None:
            self.init_message_widget()

        if self.timer.isActive():
            self.timer.stop()

        self.message_label.setProperty("class", message_type)
        self.message_label.setText(text)
        self.message_label.style().polish(self.message_label)

        if timeout > 0:
            self.timer.start(timeout)

    def _show_default(self):
        """Mostra a mensagem padrão"""
        if self.default_message and self.message_widget:
            text, message_type = self.default_message
            self.message_label.setProperty("class", message_type)
            self.message_label.setText(text)
            self.message_label.style().polish(self.message_label)

    def _restore_default(self):
        """Restaura a mensagem padrão após timeout"""
        self._show_default()

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