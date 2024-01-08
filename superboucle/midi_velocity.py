from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QRectF, QEvent
from superboucle.scrollable_graphics_view import ScrollableGraphicsView
from superboucle.clip_midi import MidiClip
from superboucle.midi_note_graphics import MidiVelocityItem

BEAT_PER_BAR = 4

class MidiVelocityScene(QGraphicsScene):
    def __init__(self, parent, clip):
        super().__init__(parent)
        self.clip = clip
        self.drag_origin = None
        self.initial_note = None

    
    def snap_delta_to_grid(self, delta):
        snap_interval = int(self.sceneRect().height() / 128)
        y = round(delta.y() / snap_interval) * snap_interval
        delta.setY(y)

    def getDialog(self):
        return self.parent().parent().parent()
        
    def getTool(self):
        return self.getDialog().getTool()

    def getSelectedItem(self):
        items = self.selectedItems()
        items = [i for i in items if isinstance(i, MidiVelocityItem)]
        return items[0] if len(items) else None

    # Enter move/resize
    def mousePressEvent(self, event):
        #print("PRESS %s" % event.scenePos().y())
        if event.button() == Qt.LeftButton and self.getSelectedItem():
            self.drag_origin = event.scenePos()
            self.initial_note = self.getSelectedItem().note.copy()

    # Move
    def mouseMoveEvent(self, event):
        if self.drag_origin is not None:
            #print("MOVE %s->%s" % (self.drag_origin.y(), event.scenePos().y()))
            # First snap movement to the grid
            delta = event.scenePos() - self.drag_origin
            self.snap_delta_to_grid(delta)
            # Change Internal Note 
            snap_interval = int(self.sceneRect().height() / 128)
            new_velocity = int(self.initial_note.velocity - (delta.y() / snap_interval))
            item = self.getSelectedItem()
            item.note.velocity = max(0, min(new_velocity, 127))
            # Change GUI
            print(item.note)
            print(delta.y())
            item.setRect(item.generateRect())

    def mouseReleaseEvent(self, event):
        if self.drag_origin is not None:
            self.drag_origin = None
            self.initial_note = None
            # trigger compute of MIDI events on midi clip
            self.clip.computeEvents()

class MidiVelocityWidget(ScrollableGraphicsView):

    def __init__(self, parent, clip, width, height):
        super().__init__(parent, width, height)
        # use custom scene
        self.scene = MidiVelocityScene(self, clip)
        self.scene.setSceneRect(QRectF(0, 0, width, height))
        self.setScene(self.scene)
        self.clip: MidiClip = clip
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        beat_width = self.width / self.clip.length

        for beat in range(self.clip.length):
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
