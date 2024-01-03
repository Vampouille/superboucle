from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QColor, QBrush
from superboucle.clip_midi import MidiNote
from superboucle.scrollable_graphics_view import ScrollableGraphicsView

BEAT_PER_BAR = 4

class PianoGridWidget(ScrollableGraphicsView):
    def __init__(self, parent, width, height, octaves, beats):
        super().__init__(parent, width, height, buffer=2)

        self.octaves: int = octaves
        self.beats: int = beats
        black_key_brush = QBrush(QColor(231, 231, 231))
        white_key_brush = QBrush(QColor(243, 243, 243))
        self.note_brush = QBrush(QColor(0, 255, 0))

        # 7 octaves: 7x12=84
        notes = self.octaves * 12
        self.note_height = int(self.height / notes)

        # Draw rectangle for notes
        for note in range(0, notes):
            y = note * self.note_height
            rect: QGraphicsRectItem = self.scene.addRect(0, int(self.height - y - self.note_height), 
                                                         self.width, self.note_height)
            if note % 12 in {1, 3, 6, 8, 10}:  # Indices of black keys
                rect.setBrush(black_key_brush)
            else:
                rect.setBrush(white_key_brush)

        # Draw horizontal line
        for note in range(0, notes):
            y = int(self.height - note * self.note_height)
            self.scene.addLine(0,
                               y,
                               self.width, 
                               y,
                               self.bar_pen if note % 12 == 0 else self.beat_pen)

        # Draw vertical line for beats
        beat_width = self.width / self.beats
        for beat in range(beats):
            x = int(beat * beat_width)
            self.scene.addLine(x,
                               2, 
                               x, 
                               self.height, 
                               self.bar_pen if beat % BEAT_PER_BAR == 0 else self.beat_pen)

    def connect(self, callback):
        self.horizontalScrollBar().valueChanged.connect(callback)
        self.verticalScrollBar().valueChanged.connect(callback)
    
    def addNote(self, note: MidiNote) -> None:
        x = self.ticksToX(note.start_tick)
        width = self.ticksToX(note.length)
        y = self.midiPitchToY(note.pitch)

        self.scene.addRect(x, y, width, self.note_height, brush=self.note_brush)
        
    def ticksToX(self, ticks: int) -> int:
        return (ticks * self.width) / (self.beats * 24)

    def midiPitchToY(self, pitch: int) -> int:
        y = (pitch - 12) * self.note_height
        return int(self.height - y - self.note_height)