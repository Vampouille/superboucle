from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt
from superboucle.scrollable_graphics_view import ScrollableGraphicsView
from superboucle.clip_midi import MidiClip

BEAT_PER_BAR = 4

class MidiVelocityWidget(ScrollableGraphicsView):

    def __init__(self, parent, clip, width, height):
        super().__init__(parent, width, height)

        self.clip: MidiClip = clip
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

    # Enter move/resize
    def mousePressEvent(self, event):
        if (self.getTool() == "select" and
            event.button() == Qt.LeftButton and
            self.isSelected()):
            self.drag_origin = event.pos()
            self.initial_note = self.note.copy()
        else:
            super().mousePressEvent(event)

    # Move
    def mouseMoveEvent(self, event):
        if self.drag_origin is not None:
            # First snap movement to the grid
            delta = event.pos() - self.drag_origin
            self.snap_delta_to_grid(delta)
            # Change Internal Note 
            new_velocity = int(self.initial_note.velocity - (delta.y() / self.vertical_snap))
            self.note.velocity = max(0, min(new_velocity, 127))
            # Change GUI
            print(self.note)
            self.setRect(self.generateRect())

    def mouseReleaseEvent(self, event):
        if self.drag_origin is not None:
            self.drag_origin = None
            self.initial_note = None
            # trigger compute of MIDI events on midi clip
            self.clip.computeEvents()

