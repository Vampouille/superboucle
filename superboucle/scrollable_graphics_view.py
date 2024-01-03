from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt

BEAT_PER_BAR = 4

class ScrollableGraphicsView(QGraphicsView):

    def __init__(self, parent, width: int, height: int, buffer: int = 0):
        super().__init__(parent)

        self.width: int = width
        self.height: int = height
        self.setMaximumSize(width + buffer, height)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene: QGraphicsScene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.bar_line_width: int = 2
        self.beat_line_width: int = 1
        self.line_color: QColor = QColor(202, 202, 202)
        self.bar_pen: QPen = QPen(self.line_color, 2)
        self.beat_pen: QPen = QPen(self.line_color, 1)
        

    def initView(self):
        self.horizontalScrollBar().setValue(0)
        self.verticalScrollBar().setValue(0)