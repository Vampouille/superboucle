from math import cos, sin, radians

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QPointF, QTimer

PI = 3.141592653589793
TICK_PER_BEAT = 24

class BeatClockWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.tick = 0
        self.colors = {4: QColor(9, 216, 223), 8: QColor(243, 233, 0), 16: QColor(109, 217, 24), 32: QColor(223, 27, 130)}

    def paintEvent(self, event):
        self.center = self.rect().center()
        self.radius = min(self.rect().width(), self.rect().height()) / 2 - 5
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Pour des bords plus lisses

        painter.setBrush(QColor(Qt.black))
        painter.setPen(QPen(QColor(223, 27, 130), 3))
        painter.drawEllipse(self.center, self.radius, self.radius)

        # Draw first line
        for divider in self.colors.keys():
            self.drawLine(painter, self.tick, divider, self.colors[divider])
        painter.end()
    
    def drawLine(self, painter, tick, divider, color):
        line_length = self.radius * 0.9
        beat = (tick / TICK_PER_BEAT) % divider 
        angle_radians = 2 * PI - (2 * PI * (beat / divider))
        end_point = QPointF(self.center.x() + line_length * cos(angle_radians + PI/2),
                            self.center.y() - line_length * sin(angle_radians + PI/2))
        painter.setPen(QPen(color, 5, cap=Qt.RoundCap))
        painter.drawLine(self.center, end_point)
