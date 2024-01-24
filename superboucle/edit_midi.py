# 5 pixel per tick
# 24*5=120 pixel per beat
# Quantize:
# 1/4: 24/4: quantize on 6 tick : 30 pixel
# 1/2: 24/2: quantize on 12 tick: 60 pixel
# 1/3: 24/3: quantize on 8 tick : 40 pixel
# 1/6: 24/6: quantize on 4 tick : 20 pixel


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QApplication,
    QWidget,
)
from superboucle.piano_grid import PianoGridWidget
from superboucle.piano_keyboard import PianoKeyboardWidget
from superboucle.beat_legend import BeatLegendWidget
from superboucle.midi_velocity import MidiVelocityWidget
from superboucle.clip_midi import MidiClip
from superboucle.edit_midi_button import EditMidiButton


TICK_PER_BEAT = 24


class EditMidiDialog(QDialog):
    def __init__(self, gui, song, cell):
        super().__init__(gui)

        self.song = song
        self.clip: MidiClip = cell.clip
        self.cell = cell
        self.beat_legend_height = 20
        keyboard_width = 40
        self.keyboard_octaves = 7
        self.velocity_height = 128
        #grid_width = 1000
        # Try to find a size to avoid aliasing 
        # 7 white keys per octave (to display in the piano keyboard)
        # 12 keys per octave (to display on the grid)
        # 7 octaves available
        self.horizontal_scale = 3 # horizontal zoom: pixel per MIDI Clock Tick
        vertical_scale = 2 # vertical zoom, note width
        self.grid_height = 7 * 12 * self.keyboard_octaves * vertical_scale
        self.grid_width = 24 * self.clip.length * self.horizontal_scale

        # Root Layout with:
        # * button
        # * body
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0,0,0,0)
        self.buttons = EditMidiButton(self, gui)
        root_layout.addWidget(self.buttons)

        # Body Widget:
        # * piano keyboard
        # * piano grid
        body_widget = QWidget()
        self.body_layout: QGridLayout = QGridLayout(body_widget)
        self.body_layout.setSpacing(0)
        self.body_layout.setContentsMargins(10,0,10,10)

        # Note Grid
        self.piano_grid: PianoGridWidget = None

        # Piano Keyboard
        self.piano_keyboard: PianoKeyboardWidget = PianoKeyboardWidget(self, self.keyboard_octaves, keyboard_width, self.grid_height)
        self.piano_keyboard.connect(self.syncScrollArea)

        # Beat Legend
        self.beat_legend: BeatLegendWidget = None

        # Velocity
        self.velocity: MidiVelocityWidget = None

        # Insert widgets in the dialog
        self.body_layout.addWidget(self.piano_keyboard, 1, 0, Qt.AlignmentFlag.AlignRight)
        self.body_layout.setColumnStretch(1, 1)
        self.body_layout.setRowStretch(1, 4)

        root_layout.addWidget(body_widget)
        root_layout.setStretch(1, 1)

        self.setWindowTitle("Edit MIDI Notes")
         # Positionner le dialogue sur le même écran que la fenêtre principale
        self.setGeometry(100, 100, 1200, 600)
        if self.parent():
            parent_geometry = self.parent().geometry()
            desktop = QApplication.desktop()
            screen_number = desktop.screenNumber(parent_geometry.center())
            screen_geometry = desktop.screenGeometry(screen_number)

            # Ajuster la position du dialogue en fonction de la fenêtre principale
            self.move(screen_geometry.center() - self.rect().center())

        self.updateUI()
        self.show()
        #self.beat_legend.initView()
    
    def getHorizontalSnap(self) -> int:
        return self.buttons.getTickSnap() * self.horizontal_scale

    def syncScrollArea(self, value):
        sender = self.sender()
        if sender == self.piano_keyboard.verticalScrollBar():
            self.piano_grid.verticalScrollBar().setValue(value)
        elif sender == self.piano_grid.verticalScrollBar():
            self.piano_keyboard.verticalScrollBar().setValue(value)
        elif sender == self.beat_legend.horizontalScrollBar():
            self.piano_grid.horizontalScrollBar().setValue(value)
            self.velocity.horizontalScrollBar().setValue(value)
        elif sender == self.piano_grid.horizontalScrollBar():
            self.beat_legend.horizontalScrollBar().setValue(value)
            self.velocity.horizontalScrollBar().setValue(value)
        elif sender == self.velocity.horizontalScrollBar():
            self.beat_legend.horizontalScrollBar().setValue(value)
            self.piano_grid.horizontalScrollBar().setValue(value)

    def updateUI(self):
        # the smallest step on x axis should be a midi clock tick
        # with 24 tick per beat 
        self.grid_width = 24 * self.clip.length * self.horizontal_scale
        
        # Beat Legend
        if self.beat_legend is not None:
            self.body_layout.removeWidget(self.beat_legend)
        self.beat_legend: BeatLegendWidget = BeatLegendWidget(self, self.grid_width, self.beat_legend_height, self.clip.length)
        self.beat_legend.connect(self.syncScrollArea)
        self.body_layout.addWidget(self.beat_legend, 0, 1, Qt.AlignmentFlag.AlignBottom)

        # Velocity
        if self.velocity is not None:
            self.body_layout.removeWidget(self.velocity)
        self.velocity: MidiVelocityWidget = MidiVelocityWidget(self, self.clip, self.grid_width, self.velocity_height, self.horizontal_scale)
        self.velocity.connect(self.syncScrollArea)
        self.body_layout.addWidget(self.velocity, 2, 1, Qt.AlignmentFlag.AlignTop)

        # Note Grid
        if self.piano_grid is not None:
            self.body_layout.removeWidget(self.piano_grid)
        self.piano_grid = PianoGridWidget(self, self.velocity.scene, self.clip, self.grid_width, self.grid_height, self.keyboard_octaves)
        self.piano_grid.connect(self.syncScrollArea)
        self.body_layout.addWidget(self.piano_grid, 1, 1)
