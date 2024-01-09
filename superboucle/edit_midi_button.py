from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QSpinBox, QComboBox, QAbstractSpinBox, QGraphicsScene, QToolButton, QHBoxLayout
from superboucle.midi_note_graphics import MidiNoteItem
 
QUANTIZE_DIVISERS = [24, 2, 4, 3, 6, 12]

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

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignLeft)

        # Midi Channel
        midiChannelLabel = QLabel()
        #midiChannelLabel.setGeometry(QRect(0, 0, 112, 25))
        midiChannelLabel.setFont(font)
        midiChannelLabel.setStyleSheet(css)
        midiChannelLabel.setAlignment(Qt.AlignCenter)
        midiChannelLabel.setObjectName("midiChannelLabel")
        midiChannelLabel.setText("MIDI Channel")
        midiChannel = QSpinBox()
        midiChannel.setGeometry(QRect(0, 0, 42, 26))
        midiChannel.setFont(font)
        midiChannel.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        midiChannel.setMinimum(1)
        midiChannel.setMaximum(16)
        midiChannel.setObjectName("midiChannel")
        midiChannel.setValue(self.parent.clip.channel + 1)
        midiChannel.valueChanged.connect(self.onMidiChannelChange)
        layout.addWidget(midiChannelLabel)
        layout.addWidget(midiChannel)
        layout.addSpacing(20)

        # Quantize
        quantizeLabel = QLabel()
        #quantizeLabel.setGeometry(QRect(0, 0, 92, 25))
        quantizeLabel.setFont(font)
        quantizeLabel.setStyleSheet(css)
        quantizeLabel.setAlignment(Qt.AlignCenter)
        quantizeLabel.setObjectName("quantizeLabel")
        quantizeLabel.setText("Quantize")
        self.quantize: QComboBox = QComboBox()
        self.quantize.setGeometry(QRect(0, 0, 72, 25))
        self.quantize.setFont(font)
        self.quantize.setCurrentText("")
        self.quantize.setObjectName("quantize")
        for div in QUANTIZE_DIVISERS:
            if div == 24:
                self.quantize.addItem("Off")
            else:
                self.quantize.addItem("1/%s" % div)
        self.quantize.currentIndexChanged.connect(self.onQuantizeChange)
        layout.addWidget(quantizeLabel)
        layout.addWidget(self.quantize)
        layout.addSpacing(20)

        # Length
        lengthLabel = QLabel()
        #lengthLabel.setGeometry(QRect(0, 0, 61, 25))
        lengthLabel.setFont(font)
        lengthLabel.setStyleSheet(css)
        lengthLabel.setAlignment(Qt.AlignCenter)
        lengthLabel.setObjectName("label_14")
        lengthLabel.setText("Length")
        length = QSpinBox()
        length.setGeometry(QRect(0, 0, 60, 26))
        length.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        length.setFont(font)
        length.setMinimum(1)
        length.setMaximum(99)
        length.setObjectName("length")
        length.setValue(self.parent.clip.length)
        length.valueChanged.connect(self.onLengthChange)
        layout.addWidget(lengthLabel)
        layout.addWidget(length)
        layout.addSpacing(20)

    def onMidiChannelChange(self, channel):
        self.parent.clip.channel = channel - 1

    def onLengthChange(self, length):
        # Set new length in the clip
        self.parent.clip.length = length
        # Re-generate piano grid widget
        self.parent.updateUI()
    
    def onQuantizeChange(self, quantize):
        #tick_round_counts = [1, 24/2, 24/4, 24/3, 24/6, 24/12]
        tick_round = int(24/QUANTIZE_DIVISERS[quantize])
        for note in self.parent.clip.notes:
            note.start_tick = round(note.start_tick / tick_round) * tick_round
            note.length = round(note.length / tick_round) * tick_round
        grid: QGraphicsScene = self.parent.piano_grid.scene
        for item in grid.items():
            if isinstance(item, MidiNoteItem):
                item.reDraw()
    
    # Return Quantization step in tick
    def getTickSnap(self):
        #tick_round_counts = [1, 24/2, 24/4, 24/3, 24/6, 24/12]
        tick_round_counts = [int(24/i) for i in QUANTIZE_DIVISERS]
        return tick_round_counts[self.quantize.currentIndex()]