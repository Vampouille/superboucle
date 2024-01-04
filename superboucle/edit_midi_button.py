from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QSpinBox, QComboBox, QAbstractSpinBox, QGraphicsScene
from superboucle.midi_note_graphics import MidiNoteItem


class EditMidiButton(QWidget):
        
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        # set font
        font = QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)

        css = "color: rgb(160, 6, 89);"

        self.setMinimumSize(QSize(530, 35))
        self.setObjectName("buttons")

        # Midi Channel
        midiChannelLabel = QLabel(self)
        midiChannelLabel.setGeometry(QRect(10, 10, 112, 25))
        midiChannelLabel.setFont(font)
        midiChannelLabel.setStyleSheet(css)
        midiChannelLabel.setAlignment(Qt.AlignCenter)
        midiChannelLabel.setObjectName("midiChannelLabel")
        midiChannelLabel.setText("MIDI Channel")
        midiChannel = QSpinBox(self)
        midiChannel.setGeometry(QRect(130, 10, 42, 26))
        midiChannel.setFont(font)
        midiChannel.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        midiChannel.setMinimum(1)
        midiChannel.setMaximum(16)
        midiChannel.setObjectName("midiChannel")
        midiChannel.setValue(self.parent.clip.channel + 1)
        midiChannel.valueChanged.connect(self.onMidiChannelChange)

        # Quantize
        quantizeLabel = QLabel(self)
        quantizeLabel.setGeometry(QRect(190, 10, 92, 25))
        quantizeLabel.setFont(font)
        quantizeLabel.setStyleSheet(css)
        quantizeLabel.setAlignment(Qt.AlignCenter)
        quantizeLabel.setObjectName("quantizeLabel")
        quantizeLabel.setText("Quantize")
        quantize: QComboBox = QComboBox(self)
        quantize.setGeometry(QRect(280, 10, 72, 25))
        quantize.setFont(font)
        quantize.setCurrentText("")
        quantize.setObjectName("quantize")
        quantize.addItem("Off")
        quantize.addItem("1/2")
        quantize.addItem("1/4")
        quantize.addItem("1/3")
        quantize.addItem("1/6")
        quantize.addItem("1/12")
        quantize.currentIndexChanged.connect(self.onQuantizeChange)

        # Length
        lengthLabel = QLabel(self)
        lengthLabel.setGeometry(QRect(380, 10, 61, 25))
        lengthLabel.setFont(font)
        lengthLabel.setStyleSheet(css)
        lengthLabel.setAlignment(Qt.AlignCenter)
        lengthLabel.setObjectName("label_14")
        lengthLabel.setText("Length")
        length = QSpinBox(self)
        length.setGeometry(QRect(450, 10, 60, 26))
        length.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        length.setFont(font)
        length.setMinimum(1)
        length.setMaximum(99)
        length.setObjectName("length")
        length.setValue(self.parent.clip.length)
        length.valueChanged.connect(self.onLengthChange)
    
    def onMidiChannelChange(self, channel):
        self.parent.clip.channel = channel - 1

    def onLengthChange(self, length):
        # Set new length in the clip
        self.parent.clip.length = length
        # Re-generate piano grid widget
        self.parent.updateUI()
    
    def onQuantizeChange(self, quantize):
        tick_round_counts = [1, 24/2, 24/4, 24/3, 24/6, 24/12]
        tick_round = int(tick_round_counts[quantize])
        for note in self.parent.clip.notes:
            note.start_tick = round(note.start_tick / tick_round) * tick_round
            note.length = round(note.length / tick_round) * tick_round
        grid: QGraphicsScene = self.parent.piano_grid.scene
        for item in grid.items():
            if isinstance(item, MidiNoteItem):
                print(type(item))
                item.setRect(item.generateRect())