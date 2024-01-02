from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush

BEAT_PER_BAR = 4

class PianoGridWidget(QWidget):
    def __init__(self, parent, width, height):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.setFixedSize(width, height)

    def paintEvent(self, event):
        black_key_color = QColor(231, 231, 231)
        white_key_color = QColor(243, 243, 243)
        line_color = QColor(202, 202, 202)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Améliorer la qualité du rendu

        # Add rectangle for notes
        # 7 octaves: 7x12=84
        notes = 84
        # Hauteur d'une note
        note_height = int(self.height / notes)
        painter.setPen(QPen(line_color, 2))

        for note in range(0, notes):  # Start from C0 (MIDI number 12)
            y = note * note_height  # Adjustment to compensate for the offset

            # Set the color based on the note (black or white)
            if note % 12 in {1, 3, 6, 8, 10}:  # Indices of black keys
                painter.setBrush(QBrush(black_key_color))
            else:
                painter.setBrush(QBrush(white_key_color))
            painter.drawRect(0, int(self.height - y - note_height), self.width, note_height)

        # Add octave separator
        octave_width = self.height / (notes / 12)
        octave_line_color = QColor(187, 187, 187)
        painter.setPen(QPen(octave_line_color, 3))
        for octave in range(int(notes / 12)):
            y = int(octave * octave_width)
            painter.drawLine(0, y, self.width, y)

        # Add vertical line for beats
        beats = 16
        beat_width = self.width / beats
        beat_line_color = QColor(171, 171, 171)
        bar_pen = QPen(beat_line_color, 2)
        beat_pen = QPen(beat_line_color, 1)

        for beat in range(beats + 1):
            x = beat * beat_width
            painter.setPen(bar_pen if beat % BEAT_PER_BAR == 0 else beat_pen)
            painter.drawLine(int(x), 0, 
                             int(x), self.height)
