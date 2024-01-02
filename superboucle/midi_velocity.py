from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QFont, QColor, QPen
from PyQt5.QtCore import Qt

BEAT_PER_BAR = 4

class MidiVelocityWidget(QGraphicsView):

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
        bar_pen = QPen(beat_line_color, 2)
        beat_pen = QPen(beat_line_color, 1)

        for beat in range(beats):
            x = beat * beat_width
            self.scene.addLine(int(x),
                               2, 
                               int(x), 
                               self.height, 
                               bar_pen if beat % BEAT_PER_BAR == 0 else beat_pen)
        
        for i in range(8):
            y = i * (self.height / 8)
            self.scene.addLine(0,
                               y, 
                               self.width, 
                               y, 
                               beat_pen)


        # Draw last bar line
        self.scene.addLine(self.width, 0, self.width, self.height, bar_pen)
        self.setScene(self.scene)

    def initView(self):
        self.horizontalScrollBar().setValue(0)
        
    def connect(self, callback):
        self.horizontalScrollBar().valueChanged.connect(callback)

