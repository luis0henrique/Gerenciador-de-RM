from PyQt5.QtWidgets import (QGraphicsDropShadowEffect, QDesktopWidget, QLabel,
                            QHBoxLayout, QVBoxLayout, QWidget, QTableWidget)
from PyQt5.QtCore import Qt, QTimer
from typing import Optional, Tuple, Union

# Constantes para tipos de mensagem
MESSAGE_DEFAULT = "default"
MESSAGE_SUCCESS = "success"
MESSAGE_ERROR = "error"
MESSAGE_WARNING = "warning"

class CenterWindowMixin:
    def center_window(self) -> None:
        """Centraliza a janela na tela."""
        frame_geometry = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

class MessageHandler:
    def __init__(self, parent_widget: QWidget, layout: Union[QVBoxLayout, QHBoxLayout]):
        """ Inicializa o manipulador de mensagens."""
        self.parent = parent_widget
        self.layout = layout
        self.message_widget: Optional[QWidget] = None
        self.message_label: Optional[QLabel] = None
        self.default_message: Optional[Tuple[str, str]] = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._restore_default)

    def init_message_widget(self, position: Optional[int] = None) -> None:
        """Inicializa o widget de mensagem na posição especificada."""
        if self.message_widget is None:
            self.message_widget = QWidget()
            self.message_widget.setObjectName("messageWidget")
            layout = QHBoxLayout(self.message_widget)
            layout.setContentsMargins(0, 5, 0, 5)

            self.message_label = QLabel()
            self.message_label.setObjectName("messageLabel")
            self.message_label.setProperty("class", MESSAGE_DEFAULT)
            self.message_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.message_label)

            if position is not None:
                self.layout.insertWidget(position, self.message_widget)
            else:
                self.layout.addWidget(self.message_widget)

            self.message_widget.setVisible(True)

    def set_default_message(self, text: str, message_type: str = MESSAGE_DEFAULT) -> None:
        """Define a mensagem padrão que será mostrada quando não houver outras"""
        self.default_message = (text, message_type)
        self._show_default()

    def show_message(self, text: str, message_type: str = MESSAGE_DEFAULT,
                    timeout: int = 0) -> None:
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

    def _show_default(self) -> None:
        """Mostra a mensagem padrão."""
        if self.default_message and self.message_widget:
            text, message_type = self.default_message
            self.message_label.setProperty("class", message_type)
            self.message_label.setText(text)
            self.message_label.style().polish(self.message_label)

    def _restore_default(self) -> None:
        """Restaura a mensagem padrão após timeout."""
        self._show_default()

class TableNavigationMixin:
    """Mixin para adicionar navegação personalizada em tabelas."""

    def handle_table_key_press(self, event, table: QTableWidget) -> None:
        """Gerencia navegação personalizada em tabelas."""
        key = event.key()

        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
            self._move_to_next_cell(table)
        elif key == Qt.Key_Backtab:
            self._move_to_previous_cell(table)
        else:
            QTableWidget.keyPressEvent(table, event)

    def _move_to_next_cell(self, table: QTableWidget) -> None:
        """Move para a próxima célula ou linha"""
        current_row = table.currentRow()
        current_col = table.currentColumn()

        if current_col < table.columnCount() - 1:
            table.setCurrentCell(current_row, current_col + 1)
        elif current_row < table.rowCount() - 1:
            table.setCurrentCell(current_row + 1, 0)

    def _move_to_previous_cell(self, table: QTableWidget) -> None:
        """Move para a célula ou linha anterior"""
        current_row = table.currentRow()
        current_col = table.currentColumn()

        if current_col > 0:
            table.setCurrentCell(current_row, current_col - 1)
        elif current_row > 0:
            table.setCurrentCell(current_row - 1, table.columnCount() - 1)

def add_shadow(widget: QWidget, blur: int = 5, x_offset: int = 1,
              y_offset: int = 1, color: Qt.GlobalColor = Qt.gray) -> None:
    """Adiciona efeito de sombra a um widget.

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