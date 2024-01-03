from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QFont, QColor, QPen
from PyQt5.QtCore import Qt
from superboucle.scrollable_graphics_view import ScrollableGraphicsView

MARGIN = 2
BEAT_PER_BAR = 4

class BeatLegendWidget(ScrollableGraphicsView):

    def __init__(self, parent, width, height, beats):
        super().__init__(parent, width, height, buffer=2)

        beat_width = self.width / beats
        font = QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)

        for beat in range(beats):
            x = int(beat * beat_width)
            if beat % BEAT_PER_BAR == 0:
                # Draw a 'bar' line
                self.scene.addLine(x, 2, x, self.height, self.bar_pen)
                text_item = self.scene.addText(str((beat // BEAT_PER_BAR) + 1), font=font)
                text_item.setPos(x + MARGIN, 1)
            else:
                # Draw a 'beat' line
                self.scene.addLine(x, (self.height / 2) + 2, x, self.height, self.beat_pen)
        # Draw last bar line
        self.scene.addLine(self.width, 0,
                           self.width, self.height,
                           self.bar_pen)

    def connect(self, callback):
        self.horizontalScrollBar().valueChanged.connect(callback)
