from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QDesktopWidget
from PyQt5.QtCore import Qt

class CenterWindowMixin:
    def center_window(self):
        """Centraliza a janela na tela"""
        frame_geometry = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

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