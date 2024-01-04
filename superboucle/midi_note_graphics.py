from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsScene
from PyQt5.QtGui import QColor, QPen 
from PyQt5.QtCore import Qt, QRectF, QPointF
from superboucle.clip_midi import MidiNote, MidiClip

TICK_PER_BEAT = 24
NOTE_PER_OCTAVE = 12

class MidiNoteItem(QGraphicsRectItem):
    def __init__(self, scene: QGraphicsScene, clip: MidiClip, note: MidiNote, scene_octaves: int):
        self.scene: QGraphicsScene = scene
        self.clip: MidiClip = clip
        self.note: MidiNote = note
        self.scene_octaves: int = scene_octaves
        self.border:int = 0
        fill_color:QColor = QColor(0, 0, 255)
        stroke_color: QColor = QColor(123,17,54)

        self.tick_width: int = int(scene.sceneRect().width() / (TICK_PER_BEAT * self.clip.length))
        # horizontal grid is snap to MIDI clock ticks
        self.horizontal_snap: int = int(scene.sceneRect().width() / (TICK_PER_BEAT * self.clip.length))
        self.vertical_snap: int  = int(scene.sceneRect().height() / (NOTE_PER_OCTAVE * scene_octaves))
        super().__init__(self.generateRect())
        self.setPen(QPen(stroke_color, self.border))
        self.setBrush(fill_color)
        self.drag_origin: QPointF = None
        self.resize_started = False
        self.initial_note = None
        self.resize_handle_width = 10

        # Définir les propriétés du déplacement et du redimensionnement
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

    # Draw Rectangle from note definition
    def generateRect(self) -> QRectF:
        x = self.tick_width * self.note.start_tick + self.border
        # note pitch start at C-2 but GUI start at C0, this is why there is -24 offset
        y = self.vertical_snap * (self.note.pitch - 24)
        y = self.scene.sceneRect().height() - y - self.vertical_snap
        width = self.tick_width * self.note.length - self.border
        return QRectF(x, y, width, self.vertical_snap)

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

    # Customize mouse pointer
    def hoverMoveEvent(self, event):
        if self.isResizingHandleHovered(event.pos()):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.DragMoveCursor)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)

    # Enter move/resize
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_origin = event.pos()
            self.initial_note = self.note.copy()
            dialog = self.scene.parent().parent().parent()
            tick_snap = dialog.buttons.getTickSnap()
            self.horizontal_snap: int = int((self.scene.sceneRect().width() * tick_snap) / (TICK_PER_BEAT * self.clip.length))
            if self.isResizingHandleHovered(event.pos()):
                self.resize_started = True

    # Move
    def mouseMoveEvent(self, event):
        # First snap movement to the grid
        delta = event.pos() - self.drag_origin
        self.snap_delta_to_grid(delta)
        # For resize only check horizontal delta
        if self.resize_started:
            # Change Internal Note 
            new_length = int(self.initial_note.length + (delta.x() / self.tick_width))
            remaining = self.clip.length * TICK_PER_BEAT - self.initial_note.start_tick
            self.note.length = max(1, min(new_length, remaining))
            # Change GUI
            self.setRect(self.generateRect())
            print("Resize in progress: %s" % self.note)
        else:
            #self.setPos(self.initial_rect.x() + delta.x(), self.initial_rect.y() + delta.y())
            #self.rect.adjust(delta.x(),delta.y(),delta.x(),delta.y())
            # Change Internal Note 
            latest_start = self.clip.length * TICK_PER_BEAT - self.initial_note.length
            new_start = int(self.initial_note.start_tick + (delta.x() / self.tick_width))
            self.note.start_tick = max(0, min(latest_start, new_start))
            lowest_note = 24
            highest_note = 24 + self.scene_octaves * NOTE_PER_OCTAVE - 1
            self.note.pitch = max(lowest_note, min(highest_note, int(self.initial_note.pitch - (delta.y() / self.vertical_snap))))
            # Change GUI
            self.setRect(self.generateRect())
            print("Move in progress: %s" % self.note)

    def mouseReleaseEvent(self, event):
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