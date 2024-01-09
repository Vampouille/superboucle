from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QColor, QPen, QWheelEvent
from PyQt5.QtCore import Qt, QRectF

BEAT_PER_BAR = 4

class ScrollableGraphicsView(QGraphicsView):

    def __init__(self, parent, width: int, height: int):
        super().__init__(parent)

        self.width: int = width
        self.height: int = height
        self.setMaximumSize(width + 2, height + 2)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene: QGraphicsScene = QGraphicsScene(self)
        self.scene.setSceneRect(QRectF(0, 0, width, height))
        self.setScene(self.scene)
        self.bar_line_width: int = 2
        self.beat_line_width: int = 1
        self.line_color: QColor = QColor(202, 202, 202)
        self.bar_pen: QPen = QPen(self.line_color, 2)
        self.beat_pen: QPen = QPen(self.line_color, 1)
        
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ShiftModifier:
            delta = int(event.angleDelta().y() / 4)
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
        else:
            super().wheelEvent(event)