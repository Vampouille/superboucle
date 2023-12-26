from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt

class PianoKeyboardWidget(QGraphicsView):

    def __init__(self, parent, width, height):
        super().__init__(parent)

        self.width = width
        self.height = height
        self.setMaximumSize(width, height)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene(self)

        # 7 octaves: 7x12=84
        notes = 84
        # number of white keys
        notes_each_color = int((notes / 12) * 7)
        # 7 white key per octave
        # So first count the number of octave
        # Then multiply by 7
        white_key_width = self.height / notes_each_color
        # The black keys are half as wide
        black_key_width = white_key_width / 2.0

        white_key_height = self.width
        # length of the black keys are 57% of the white key
        # white: 13,8 cm
        # black: 7,8  cm
        black_key_height = white_key_height * 0.57

        line_color = QColor(150, 150, 150)
        black_color = QColor(0, 0, 0)
        white_key_pen = QPen(line_color, 1)
        black_key_brush = Qt.black

        # First draw the white keys
        for i in range(notes_each_color):
            y = i * white_key_width
            self.scene.addRect(1,
                               int(self.height - y - white_key_width) + 1,
                               int(white_key_height) - 1,
                               int(white_key_width) - 1,
                               pen=white_key_pen)

        # Then draw black keys
        for i in range(notes_each_color):
            if i % 7 in { 0, 1, 3, 4, 5}:
                y = (i * white_key_width) + (white_key_width / 2)
                self.scene.addRect(0,
                                   int(self.height - y - (1.5 * black_key_width)),
                                   int(black_key_height),
                                   int(black_key_width),
                                   brush=black_key_brush)

        self.setScene(self.scene)
        
    def initView(self):
        self.verticalScrollBar().setValue(0)

    def connect(self, callback):
        self.verticalScrollBar().valueChanged.connect(callback)
