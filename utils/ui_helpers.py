from PyQt5.QtWidgets import (QGraphicsDropShadowEffect, QLabel, QHBoxLayout,
                             QVBoxLayout, QWidget, QTableWidget, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import Optional, Union
from utils.styles import get_shadow_color

# Constantes para tipos de mensagem
MESSAGE_DEFAULT = "default"
MESSAGE_SUCCESS = "success"
MESSAGE_ERROR = "error"
MESSAGE_WARNING = "warning"
MESSAGE_LOADING = "loading"
MESSAGE_SEARCH = "search"

class CenterWindowMixin:
    def center_window(self) -> None:
        """Centraliza a janela na tela usando QScreen (recomendado)."""
        frame_geometry = self.frameGeometry()
        screen = QApplication.primaryScreen()
        if not screen:
            return

        screen_geometry = screen.availableGeometry()
        center_point = screen_geometry.center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

class MessageHandler:
    def __init__(self, parent_widget: QWidget, layout: Union[QVBoxLayout, QHBoxLayout]):
        """Inicializa o manipulador de mensagens."""
        self.parent = parent_widget
        self.layout = layout
        self.message_widget: Optional[QWidget] = None
        self.message_label: Optional[QLabel] = None
        self.current_message: Optional[str] = None

        # Inicializa o widget imediatamente
        self.init_message_widget()
        self.show_message("Pronto para carregar dados", MESSAGE_DEFAULT)

    def init_message_widget(self, position: Optional[int] = None) -> None:
        """Inicializa o widget de mensagem na posição especificada."""
        if self.message_widget is None:
            self.message_widget = QWidget()
            self.message_widget.setObjectName("messageWidget")
            layout = QHBoxLayout(self.message_widget)
            layout.setContentsMargins(0, 0, 0, 0)

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

    def show_message(self, text: str, message_type: str = MESSAGE_DEFAULT) -> None:
        """Mostra uma mensagem persistente até ser substituída por outra."""
        if self.message_widget is None:
            self.init_message_widget()

        self.current_message = (text, message_type)
        self.message_label.setProperty("class", message_type)
        self.message_label.setText(text)
        self.message_label.style().polish(self.message_label)
        self.message_widget.setVisible(True)

    def show_loading(self):
        """Mostra mensagem de carregamento."""
        self.show_message("Carregando...", MESSAGE_LOADING)

    def show_error(self, message: str):
        """Mostra mensagem de erro."""
        self.show_message(message, MESSAGE_ERROR)

    def show_success(self, message: str):
        """Mostra mensagem de sucesso."""
        self.show_message(message, MESSAGE_SUCCESS)

    def show_search_results(self, count: int, by_rm: bool = False):
        """Mostra resultados de busca."""
        search_type = "RM" if by_rm else "nome"
        self.show_message(f"Busca por {search_type} encontrou {count} resultados", MESSAGE_SEARCH)

    def show_record_count(self, count: int):
        """Mostra contagem de registros."""
        self.show_message(f"Exibindo {count} registros", MESSAGE_DEFAULT)

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

class CornerSquare(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cornerSquare")
        self.setFixedSize(50, 32)  # Altura igual ao header
        self.setAlignment(Qt.AlignCenter)
        self.setText("#")

def add_shadow(
    widget: QWidget,
    blur: int = 5,
    x_offset: int = 2,
    y_offset: int = 2,
    color: Optional[QColor] = None
) -> None:
    """Adiciona efeito de sombra a um widget com cor baseada no tema.

    Args:
        widget: O widget que receberá a sombra
        blur: Raio do desfoque da sombra (default: 10)
        x_offset: Deslocamento horizontal (default: 0)
        y_offset: Deslocamento vertical (default: 0)
        color: Opcional - Cor customizada da sombra (se None, usa cor do tema)
    """
    from utils.styles import get_shadow_color  # Importação local para evitar circular

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)

    if color is None:
        color = QColor(get_shadow_color())

    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)

def update_shadows_on_theme_change(widgets: list[QWidget]) -> None:
    """Atualiza as sombras de uma lista de widgets quando o tema muda."""
    for widget in widgets:
        if widget.graphicsEffect():
            effect = widget.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                effect.setColor(QColor(get_shadow_color()))