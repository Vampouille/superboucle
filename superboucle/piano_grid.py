from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsScene
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt, QEvent, QRectF
from superboucle.clip_midi import MidiNote, MidiClip
from superboucle.scrollable_graphics_view import ScrollableGraphicsView
from superboucle.midi_note_graphics import MidiNoteItem

BEAT_PER_BAR = 4
TICK_PER_BEAT = 24

class PianoGridScene(QGraphicsScene):
    def __init__(self, parent, clip, octaves):
        super().__init__(parent)
        self.selectionChanged.connect(self.updateNoteColor)
        self.clip: MidiClip = clip
        self.octaves: int = octaves
        # 7 octaves: 7x12=84
        self.notes = self.octaves * 12

    def getDialog(self):
        return self.parent().parent().parent()
        
    def getNoteItem(self, pos):
        items = self.items(pos)
        items = [i for i in items if isinstance(i, MidiNoteItem)]
        return items[0] if len(items) else None

    def getSelectedNoteItem(self):
        items = self.selectedItems()
        items = [i for i in items if isinstance(i, MidiNoteItem)]
        return items[0] if len(items) else None

    def event(self, event):
        if event.type() == QEvent.GraphicsSceneMouseMove:
            self.handleMouseMoveEvent(event)
        return super().event(event)

    # Customize mouse pointer
    def handleMouseMoveEvent(self, event):
        item = self.getNoteItem(event.scenePos())

        if item is not None:
            if item.isResizingHandleHovered(event.scenePos()):
                # Change note length
                self.parent().setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                # Move note: pitch, timing
                self.parent().setCursor(Qt.CursorShape.DragMoveCursor)
        else:
            # Draw new note
            self.parent().setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event):
        item = self.getNoteItem(event.scenePos())
        if (event.button() == Qt.LeftButton and
            item is None and
            self.getSelectedNoteItem() is None):

            self.drawNewNote(event.scenePos())
        else:
            # Select or unselect item 
            super().mousePressEvent(event)

    def drawNewNote(self, scene_pos):
        note_height = int(self.sceneRect().height() / self.notes)
        tick_width = self.sceneRect().width() / (self.clip.length * TICK_PER_BEAT)
        pitch = int(((self.sceneRect().height() - scene_pos.y()) / note_height) + 24)
        horizontal_snap = self.getDialog().getHorizontalSnap()
        x = round(scene_pos.x() / horizontal_snap) * horizontal_snap
        start = int(x / tick_width)
        note = MidiNote(pitch, 100, start, 24)
        noteItem = MidiNoteItem(self, self.parent().velocityScene, self.clip, note, self.octaves)
        self.clip.addNote(note)
        self.addItem(noteItem)
        self.clip.computeEvents()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected_items = self.selectedItems()
            for item in selected_items:
                if isinstance(item, MidiNoteItem):
                    self.clip.removeNote(item.note)
                    item.velocityScene.removeItem(item.velocity)
                    self.removeItem(item)

        super().keyPressEvent(event)

    def updateNoteColor(self):
        selected_items = self.selectedItems()
        for item in self.items():
            if isinstance(item, MidiNoteItem):
                if item in selected_items:
                    item.applyCssForSelected()
                else:
                    item.applyCssForNotSelected()

class PianoGridWidget(ScrollableGraphicsView):
    def __init__(self, parent, velocityScene: QGraphicsScene, clip: MidiClip, width, height, octaves):
        super().__init__(parent, width, height)
        self.setMouseTracking(True)
        self.velocityScene = velocityScene

        self.drag_origin = None
        self.drawing_note = False

        self.octaves: int = octaves
        self.clip: MidiClip = clip
        black_key_brush = QBrush(QColor(231, 231, 231))
        white_key_brush = QBrush(QColor(243, 243, 243))
        self.note_brush = QBrush(QColor(0, 255, 0))

        # Replace scene with a custom one 
        self.scene = PianoGridScene(self, self.clip, self.octaves)
        self.scene.setSceneRect(QRectF(0, 0, width, height))
        self.setScene(self.scene)
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
        self.tick_width = self.scene.sceneRect().width() / (self.clip.length * TICK_PER_BEAT)
        for beat in range(self.clip.length):
            x = int(beat * beat_width)
            self.scene.addLine(x,
                               2, 
                               x, 
                               self.height, 
                               self.bar_pen if beat % BEAT_PER_BAR == 0 else self.beat_pen)
        # Draw notes from clip
        for note in self.clip.notes:
            self.scene.addItem(MidiNoteItem(self.scene, self.velocityScene, self.clip, note, self.octaves))


    def connect(self, callback):
        self.horizontalScrollBar().valueChanged.connect(callback)
        self.verticalScrollBar().valueChanged.connect(callback)