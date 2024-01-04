from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt, QRectF, QPointF
from superboucle.clip_midi import MidiNote, MidiClip
from superboucle.scrollable_graphics_view import ScrollableGraphicsView
from superboucle.midi_note_graphics import MidiNoteItem

BEAT_PER_BAR = 4

class PianoGridWidget(ScrollableGraphicsView):
    def __init__(self, parent, clip: MidiClip, width, height, octaves):
        super().__init__(parent, width, height)
        self.setMouseTracking(True)

        self.octaves: int = octaves
        self.clip: MidiClip = clip
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
        beat_width = self.width / self.clip.length
        for beat in range(self.clip.length):
            x = int(beat * beat_width)
            self.scene.addLine(x,
                               2, 
                               x, 
                               self.height, 
                               self.bar_pen if beat % BEAT_PER_BAR == 0 else self.beat_pen)
        # Draw notes from clip
        for note in self.clip.notes:
            self.scene.addItem(MidiNoteItem(self.scene, self.clip, note, self.octaves))

    # Customize mouse pointer
    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        items = [i for i in self.scene.items(scene_pos) if isinstance(i, MidiNoteItem)]
        dialog = self.scene.parent().parent().parent()

        if dialog.getTool() == "edit":
            if len(items):
                if items[0].isResizingHandleHovered(scene_pos):
                    # Change note length
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    # Move note: pitch, timing
                    self.setCursor(Qt.CursorShape.DragMoveCursor)
            else:
                # Draw new note
                self.setCursor(Qt.CursorShape.CrossCursor)
        elif dialog.getTool() == "select":
            # Select note for deletion or velocity edit
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def connect(self, callback):
        self.horizontalScrollBar().valueChanged.connect(callback)
        self.verticalScrollBar().valueChanged.connect(callback)