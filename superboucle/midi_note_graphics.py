from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene
from PyQt5.QtGui import QColor, QPen 
from PyQt5.QtCore import Qt, QRectF, QPointF
from superboucle.clip_midi import MidiNote, MidiClip

TICK_PER_BEAT = 24
NOTE_PER_OCTAVE = 12

class MidiNoteItem(QGraphicsRectItem):
    def __init__(self, scene: QGraphicsScene, velocityScene: QGraphicsScene, clip: MidiClip, note: MidiNote, scene_octaves: int):
        self.scene: QGraphicsScene = scene
        self.velocityScene: QGraphicsScene = velocityScene
        self.clip: MidiClip = clip
        self.note: MidiNote = note
        self.scene_octaves: int = scene_octaves
        self.border:int = 0
        self.fill_color:QColor = QColor(6, 147, 152)
        self.fill_color_selected:QColor = QColor(247, 42, 151)
        stroke_color: QColor = QColor(123, 17, 54)

        self.tick_width: int = int(scene.sceneRect().width() / (TICK_PER_BEAT * self.clip.length))
        # horizontal grid is snap to MIDI clock ticks
        self.horizontal_snap: int = None
        self.vertical_snap: int  = int(scene.sceneRect().height() / (NOTE_PER_OCTAVE * scene_octaves))
        super().__init__(self.generateRect())
        self.setPen(QPen(stroke_color, self.border))

        # Draw velocity rectangle
        self.velocity = MidiVelocityItem(self.velocityScene, self.clip, self.note)
        self.velocityScene.addItem(self.velocity)

        self.drag_origin: QPointF = None
        self.resize_started = False
        self.initial_note = None
        self.resize_handle_width = 10

        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        # required for focusItemChanged signal to work:
        #self.setFlag(QGraphicsRectItem.ItemIsFocusable)
        self.applyCssForNotSelected()
    
    # Synchronize selection of note and velocity items
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            #print("Note %s Value %s" % (self.note, value))
            self.velocity.setSelected(bool(value))
        return super().itemChange(change, value)

    # Draw Rectangle from note definition
    def generateRect(self) -> QRectF:
        x = self.tick_width * self.note.start_tick + self.border
        # note pitch start at C-2 but GUI start at C0, this is why there is -24 offset
        y = self.vertical_snap * (self.note.pitch - 24)
        y = self.scene.sceneRect().height() - y - self.vertical_snap
        width = self.tick_width * self.note.length - self.border
        return QRectF(x, y, width, self.vertical_snap)

    def reDraw(self):
        self.setRect(self.generateRect())
        self.velocity.setRect(self.velocity.generateRect())

    def applyCssForSelected(self):
        self.setBrush(self.fill_color_selected)
        self.velocity.applyCssForSelected()

    def applyCssForNotSelected(self):
        self.setBrush(self.fill_color)
        self.velocity.applyCssForNotSelected()

    def getDialog(self):
        return self.scene.parent().parent().parent()
        
    # Snap helpers
    def snap_to_xgrid(self, value):
        return self._snap_to_grid(value, self.horizontal_snap)

    def snap_to_ygrid(self, value):
        return self._snap_to_grid(value, self.vertical_snap)
    
    def snap_delta_to_grid(self, delta):
        delta.setX(self.snap_to_xgrid(delta.x()))
        delta.setY(self.snap_to_ygrid(delta.y()))

    def _snap_to_grid(self, value, snap_interval):
        return round(value / snap_interval) * snap_interval

    # Enter move/resize
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_origin = event.pos()
            self.initial_note = self.note.copy()
            self.horizontal_snap: int = self.getDialog().getHorizontalSnap()
            if self.isResizingHandleHovered(event.pos()):
                self.resize_started = True
        for item in self.getDialog().piano_grid.scene.selectedItems():
            item.setSelected(False)
        self.setSelected(True)
        super().mousePressEvent(event)

    # Move
    def mouseMoveEvent(self, event):
        if self.drag_origin is not None:
            # First snap movement to the grid
            delta = event.pos() - self.drag_origin
            self.snap_delta_to_grid(delta)
            # For resize only check horizontal delta
            # Change Internal Note 
            if self.resize_started:
                new_length = int(self.initial_note.length + (delta.x() / self.tick_width))
                remaining = self.clip.length * TICK_PER_BEAT - self.initial_note.start_tick
                self.note.length = max(1, min(new_length, remaining))
            else:
                latest_start = self.clip.length * TICK_PER_BEAT - self.initial_note.length
                new_start = int(self.initial_note.start_tick + (delta.x() / self.tick_width))
                self.note.start_tick = max(0, min(latest_start, new_start))
                lowest_note = 24
                highest_note = 24 + self.scene_octaves * NOTE_PER_OCTAVE - 1
                self.note.pitch = max(lowest_note, min(highest_note, int(self.initial_note.pitch - (delta.y() / self.vertical_snap))))
            # Change GUI
            self.reDraw()

    def mouseReleaseEvent(self, event):
        if self.drag_origin is not None:
            if self.resize_started:
                self.resize_started = False
            self.drag_origin = None
            self.initial_note = None
            # trigger compute of MIDI events on midi clip
            self.clip.computeEvents()

    def isResizingHandleHovered(self, pos):
        right_handle_rect = QRectF(self.rect().right() - self.resize_handle_width, self.rect().top(),
                                   self.resize_handle_width, self.rect().height())
        return self.resize_started or right_handle_rect.contains(pos)

class MidiVelocityItem(QGraphicsRectItem):
    def __init__(self, scene: QGraphicsScene, clip: MidiClip, note: MidiNote):
        self.scene: QGraphicsScene = scene
        self.clip: MidiClip = clip
        self.note: MidiNote = note
        self.border:int = 0
        self.fill_color:QColor = QColor(6, 147, 152, 50)
        self.fill_color_selected:QColor = QColor(247, 42, 151)
        stroke_color: QColor = QColor(123, 17, 54, 50)

        # horizontal grid is snap to MIDI clock ticks
        self.vertical_snap: int  = int(scene.sceneRect().height() / 128)
        super().__init__(self.generateRect())
        self.setPen(QPen(stroke_color, self.border))
        self.applyCssForNotSelected()

        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        # required for focusItemChanged signal to work:
        self.setFlag(QGraphicsRectItem.ItemIsFocusable)

    # Draw Rectangle from note velocity
    def generateRect(self) -> QRectF:
        x = self.scene.tick_width * self.note.start_tick + self.border
        # note pitch start at C-2 but GUI start at C0, this is why there is -24 offset
        y = max(0, self.vertical_snap * self.note.velocity)
        y = self.scene.sceneRect().height() - y
        width = self.scene.tick_width * self.note.length - self.border
        height = self.scene.sceneRect().height() - y
        return QRectF(x, y, width, height)

    def applyCssForSelected(self):
        self.setBrush(self.fill_color_selected)

    def applyCssForNotSelected(self):
        self.setBrush(self.fill_color)