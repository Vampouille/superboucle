from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap
from PyQt5.QtWidgets import QWidget

WIDTH = 600
HEIGHT = 50
TICK_HEIGHT = 10
START = -30
STOP = 30
STEP = 5

class TapeSpeedVisualWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(WIDTH, HEIGHT)
        self.speed = 0

        # Create a QPixmap for the background
        self.background_pixmap = QPixmap(self.width(), self.height())
        self.background_pixmap.fill(QColor(211, 211, 211))  # Fill with light gray
        self.draw_background()
        self.update()

    def set_speed(self, speed):
        self.speed = speed
        self.update()

    def draw_background(self):
        painter = QPainter(self.background_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 2))

        step = WIDTH / (STOP - START)
        for i in range(START, STOP+1, STEP):
            v = i
            i -= START
            i *= step 
            painter.drawLine(QPointF(i, 0), QPointF(i, TICK_HEIGHT))
            painter.drawLine(QPointF(i, HEIGHT - TICK_HEIGHT), QPointF(i, HEIGHT))
            painter.drawText(int(i), TICK_HEIGHT + 2, 20, 20, Qt.AlignHCenter | Qt.AlignVCenter, str(v))

        painter.end()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, self.background_pixmap)
        painter.setPen(QPen(QColor(240, 0, 0), 2))

        # Normalize value
        speed_normalize = min(STOP, max(START, self.speed))
        speed_pos = ((speed_normalize - START) / (STOP - START)) * WIDTH
        # Draw Line
        painter.drawLine(QPointF(speed_pos, 0), QPointF(speed_pos, HEIGHT))