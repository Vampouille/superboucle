from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt
from superboucle.scrollable_graphics_view import ScrollableGraphicsView

BEAT_PER_BAR = 4

class MidiVelocityWidget(ScrollableGraphicsView):

    def __init__(self, parent, width, height, beats):
        super().__init__(parent, width, height, buffer=2)

        beat_width = self.width / beats

        for beat in range(beats):
            x = beat * beat_width
            self.scene.addLine(int(x),
                               2, 
                               int(x), 
                               self.height, 
                               self.bar_pen if beat % BEAT_PER_BAR == 0 else self.beat_pen)
        
        for i in range(8):
            y = i * (self.height / 8)
            self.scene.addLine(0,
                               y, 
                               self.width, 
                               y, 
                               self.beat_pen)


        # Draw last bar line
        self.scene.addLine(self.width, 0, self.width, self.height, self.bar_pen)

    def connect(self, callback):
        self.horizontalScrollBar().valueChanged.connect(callback)

