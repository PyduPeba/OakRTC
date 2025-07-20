from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor
import sys

class OverlayWindow(QWidget):
    def __init__(self, square_pos=(100, 100), square_size=(64, 64)):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Não click-through!
        self.square_pos = square_pos
        self.square_size = square_size
        self.resize(800, 600)  # Tamanho da janela overlay

    def update_square(self, pos, size):
        self.square_pos = pos
        self.square_size = size
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor(0, 200, 255, 100)  # Azul transparente
        painter.setBrush(color)
        painter.setPen(Qt.GlobalColor.black)
        x, y = self.square_pos
        w, h = self.square_size
        painter.drawRect(x, y, w, h)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    overlay.show()

    # Teste: mover e redimensionar o quadrado depois de 2s
    def move_square():
        # Suponha: cada sqm = 32 pixels
        # Exemplo de "waypoint" a 5 sqms à direita e 3 para baixo do topo-esquerdo da overlay
        offset_x = 5 * 32
        offset_y = 3 * 32
        # Exemplo de range 2x2 sqm
        overlay.update_square((offset_x, offset_y), (2 * 32, 2 * 32))

    from PyQt6.QtCore import QTimer
    QTimer.singleShot(2000, move_square)

    sys.exit(app.exec())
