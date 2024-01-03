# 5 pixel per tick
# 24*5=120 pixel per beat
# Quantize:
# 1/4: 24/4: quantize on 6 tick : 30 pixel
# 1/2: 24/2: quantize on 12 tick: 60 pixel
# 1/3: 24/3: quantize on 8 tick : 40 pixel
# 1/6: 24/6: quantize on 4 tick : 20 pixel


from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QScrollBar,
    QWidget,
    QLabel,
    QSpinBox,
    QComboBox,
    QAbstractSpinBox,
    QPushButton,
)
from superboucle.piano_grid import PianoGridWidget
from superboucle.piano_keyboard import PianoKeyboardWidget
from superboucle.beat_legend import BeatLegendWidget
from superboucle.midi_velocity import MidiVelocityWidget
from superboucle.clip_midi import MidiClip


class CustomScrollBar(QScrollBar):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)


class EditMidiDialog(QDialog):
    def __init__(self, parent, clip: MidiClip):
        super().__init__(parent)

        self.clip: MidiClip = clip
        beat_legend_height = 20
        keyboard_width = 40
        keyboard_octaves = 7
        velocity_height = 150
        beats = 16
        # the smallest step on x axis should be a midi clock tick
        # with 24 tick per beat 
        horizontal_scale = 3
        grid_width = 24 * beats * horizontal_scale
        #grid_width = 1000
        # Try to find a size to avoid aliasing 
        # 7 white keys per octave (to display in the piano keyboard)
        # 12 keys per octave (to display on the grid)
        # 7 octaves available
        vertical_scale = 2 # vertical zoom, note width
        grid_height = 7 * 12 * keyboard_octaves * vertical_scale

        # Root Layout with:
        # * button
        # * body
        root_layout = QVBoxLayout(self)
        root_layout.addWidget(self.generateButton())

        # Body Widget:
        # * piano keyboard
        # * piano grid
        body_widget = QWidget()
        body_layout = QGridLayout(body_widget)
        body_layout.setSpacing(0)

        # Note Grid
        self.piano_grid: PianoGridWidget = PianoGridWidget(self, grid_width, grid_height, keyboard_octaves, beats)
        self.piano_grid.connect(self.syncScrollArea)

        # Piano Keyboard
        self.piano_keyboard: PianoKeyboardWidget = PianoKeyboardWidget(self, keyboard_width, grid_height)
        self.piano_keyboard.connect(self.syncScrollArea)

        # Beat Legend
        self.beat_legend: BeatLegendWidget = BeatLegendWidget(self, grid_width, beat_legend_height, beats)
        self.beat_legend.connect(self.syncScrollArea)

        # Velocity
        self.velocity: MidiVelocityWidget = MidiVelocityWidget(self, grid_width, velocity_height, beats)
        self.velocity.connect(self.syncScrollArea)

        # Insert widgets in the dialog
        body_layout.addWidget(self.beat_legend, 0, 1, Qt.AlignmentFlag.AlignBottom)
        body_layout.addWidget(self.piano_keyboard, 1, 0, Qt.AlignmentFlag.AlignRight)
        body_layout.addWidget(self.piano_grid, 1, 1)
        body_layout.addWidget(self.velocity, 2, 1, Qt.AlignmentFlag.AlignTop)
        body_layout.setColumnStretch(1, 1)
        body_layout.setRowStretch(1, 4)

        root_layout.addWidget(body_widget)
        root_layout.setStretch(1, 1)

        self.setWindowTitle("Edit MIDI Notes")
        self.setGeometry(100, 100, 800, 600)
        self.show()
        self.beat_legend.initView()
        self.drawNotes()

    def drawNotes(self) -> None:
        for note in self.clip.notes:
            self.piano_grid.addNote(note)

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

    def generateButton(self):
        # set font
        font = QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)

        css = "color: rgb(160, 6, 89);"

        widget = QWidget()
        widget.setMinimumSize(QSize(530, 35))
        widget.setObjectName("buttons")

        # Midi Channel
        self.midiChannelLabel = QLabel(widget)
        self.midiChannelLabel.setGeometry(QRect(10, 10, 112, 25))
        self.midiChannelLabel.setFont(font)
        self.midiChannelLabel.setStyleSheet(css)
        self.midiChannelLabel.setAlignment(Qt.AlignCenter)
        self.midiChannelLabel.setObjectName("midiChannelLabel")
        self.midiChannelLabel.setText("MIDI Channel")
        self.midiChannel = QSpinBox(widget)
        self.midiChannel.setGeometry(QRect(130, 10, 42, 26))
        self.midiChannel.setFont(font)
        self.midiChannel.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.midiChannel.setMinimum(1)
        self.midiChannel.setMaximum(16)
        self.midiChannel.setObjectName("midiChannel")

        # Quantize
        self.quantizeLabel = QLabel(widget)
        self.quantizeLabel.setGeometry(QRect(190, 10, 92, 25))
        self.quantizeLabel.setFont(font)
        self.quantizeLabel.setStyleSheet(css)
        self.quantizeLabel.setAlignment(Qt.AlignCenter)
        self.quantizeLabel.setObjectName("quantizeLabel")
        self.quantizeLabel.setText("Quantize")
        self.quantize = QComboBox(widget)
        self.quantize.setGeometry(QRect(280, 10, 72, 25))
        self.quantize.setFont(font)
        self.quantize.setCurrentText("")
        self.quantize.setObjectName("quantize")
        self.quantize.addItem("Off")
        self.quantize.addItem("1/4")
        self.quantize.addItem("1/2")
        self.quantize.addItem("1/3")
        self.quantize.addItem("1/6")

        # Length
        self.lengthLabel = QLabel(widget)
        self.lengthLabel.setGeometry(QRect(380, 10, 61, 25))
        self.lengthLabel.setFont(font)
        self.lengthLabel.setStyleSheet(css)
        self.lengthLabel.setAlignment(Qt.AlignCenter)
        self.lengthLabel.setObjectName("label_14")
        self.lengthLabel.setText("Length")
        self.length = QSpinBox(widget)
        self.length.setGeometry(QRect(450, 10, 60, 26))
        self.length.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.length.setFont(font)
        self.length.setMinimum(1)
        self.length.setMaximum(99)
        self.length.setObjectName("length")

        button = QPushButton("Cliquez-moi", widget)
        button.clicked.connect(
            self.onButtonClick
        )

        return widget

    def onButtonClick(self):
        self.beat_legend.initView()
        print("OK")