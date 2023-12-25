from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PyQt5.QtGui import QFont, QColor, QPen
from PyQt5.QtCore import Qt

MARGIN = 2
BEAT_PER_BAR = 4


class BeatLegendWidget(QGraphicsView):

    def __init__(self, parent, width, height, beats):
        super().__init__(parent)

        self.width = width
        self.height = height
        self.setMaximumSize(width, height)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene(self)

        beat_width = self.width / beats
        beat_line_color = QColor(171, 171, 171)
        pen = QPen(beat_line_color, 2)
        font = QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)


        for beat in range(beats):
            x = beat * beat_width
            if beat % BEAT_PER_BAR == 0:
                # draw a 'bar' line
                self.scene.addLine(int(x), 2, int(x), self.height, pen)
                text_item = self.scene.addText(str((beat // BEAT_PER_BAR) + 1), font=font)
                text_item.setPos(x + MARGIN, 1)
            else:
                # draw a 'beat' line
                self.scene.addLine(int(x), (self.height / 2) + 2, int(x), self.height, pen)
        # Draw last bar line
        self.scene.addLine(self.width, 0, self.width, self.height, pen)
        self.setScene(self.scene)

    def initView(self):
        self.horizontalScrollBar().setValue(0)
        
    def connect(self, callback):
        self.horizontalScrollBar().valueChanged.connect(callback)
        self.verticalScrollBar().valueChanged.connect(callback)
