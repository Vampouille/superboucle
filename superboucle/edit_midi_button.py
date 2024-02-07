from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QSpinBox, QComboBox, QAbstractSpinBox, QGraphicsScene, QHBoxLayout, QLineEdit
from superboucle.midi_note_graphics import MidiNoteItem
 
QUANTIZE_DIVISERS = [24, 2, 4, 3, 6, 12]

class EditMidiButton(QWidget):
        
    def __init__(self, parent, gui):
        super().__init__()

        self.parent = parent
        self.gui = gui

        # set font
        font = QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)

        css = "color: rgb(160, 6, 89);"

        self.setMinimumSize(QSize(530, 35))

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignLeft)

        # Clip Name
        name = QLineEdit()
        name.setFixedSize(215, 30)
        name.setFont(font)
        name.setStyleSheet("QLineEdit {background-color: black; color: rgb(255, 253, 24);}")
        name.setAlignment(Qt.AlignCenter)
        name.setText(self.parent.clip.name)
        name.textChanged.connect(self.onNameChanged)
        layout.addWidget(name)

        # Midi Channel
        midiChannelLabel = QLabel()
        #midiChannelLabel.setGeometry(QRect(0, 0, 112, 25))
        midiChannelLabel.setFont(font)
        midiChannelLabel.setStyleSheet(css)
        midiChannelLabel.setAlignment(Qt.AlignCenter)
        midiChannelLabel.setText("MIDI Channel")
        midiChannel = QSpinBox()
        midiChannel.setGeometry(QRect(0, 0, 42, 26))
        midiChannel.setFont(font)
        midiChannel.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        midiChannel.setMinimum(1)
        midiChannel.setMaximum(16)
        midiChannel.setValue(self.parent.clip.channel + 1)
        midiChannel.valueChanged.connect(self.onMidiChannelChanged)
        layout.addWidget(midiChannelLabel)
        layout.addWidget(midiChannel)
        layout.addSpacing(20)

        # Quantize
        quantizeLabel = QLabel()
        quantizeLabel.setFont(font)
        quantizeLabel.setStyleSheet(css)
        quantizeLabel.setAlignment(Qt.AlignCenter)
        quantizeLabel.setText("Quantize")
        self.quantize: QComboBox = QComboBox()
        self.quantize.setGeometry(QRect(0, 0, 72, 25))
        self.quantize.setFont(font)
        self.quantize.setCurrentText("")
        qi=None
        for i, div in enumerate(QUANTIZE_DIVISERS):
            if self.parent.clip.quantize == div:
                qi = i
            if div == 24:
                self.quantize.addItem("Off")
            else:
                self.quantize.addItem("1/%s" % div)
        self.quantize.setCurrentIndex(qi)
        self.quantize.currentIndexChanged.connect(self.onQuantizeChanged)
        layout.addWidget(quantizeLabel)
        layout.addWidget(self.quantize)
        layout.addSpacing(20)

        # Mute Group
        muteGroupLabel = QLabel()
        muteGroupLabel.setFont(font)
        muteGroupLabel.setStyleSheet(css)
        muteGroupLabel.setAlignment(Qt.AlignCenter)
        muteGroupLabel.setText("Mute Group")
        self.muteGroup: QComboBox = QComboBox()
        self.muteGroup.setGeometry(QRect(0, 0, 72, 25))
        self.muteGroup.setFont(font)
        for i in range(10):
            if i == 0:
                self.muteGroup.addItem("Off")
            else:
                self.muteGroup.addItem(str(i))
        if not self.parent.clip.mute_group:
            self.muteGroup.setCurrentText("Off")
        else:
            self.muteGroup.setCurrentText(str(self.parent.clip.mute_group))
        self.muteGroup.activated.connect(self.onMuteGroupChanged)
        layout.addWidget(muteGroupLabel)
        layout.addWidget(self.muteGroup)
        layout.addSpacing(20)

        # Length
        lengthLabel = QLabel()
        #lengthLabel.setGeometry(QRect(0, 0, 61, 25))
        lengthLabel.setFont(font)
        lengthLabel.setStyleSheet(css)
        lengthLabel.setAlignment(Qt.AlignCenter)
        lengthLabel.setText("Length")
        length = QSpinBox()
        length.setGeometry(QRect(0, 0, 60, 26))
        length.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        length.setFont(font)
        length.setMinimum(1)
        length.setMaximum(99)
        length.setValue(self.parent.clip.length)
        length.valueChanged.connect(self.onLengthChanged)
        layout.addWidget(lengthLabel)
        layout.addWidget(length)
        layout.addSpacing(20)

        # Output
        outputLabel = QLabel()
        outputLabel.setFont(font)
        outputLabel.setStyleSheet(css)
        outputLabel.setAlignment(Qt.AlignCenter)
        outputLabel.setText("Output")
        self.output: QComboBox = QComboBox()
        self.output.setGeometry(QRect(0, 0, 72, 25))
        self.output.setFont(font)
        self.output.activated.connect(self.onOutputChanged)
        self.gui.portChangeSignal.connect(self.updatePorts)
        self.updatePorts()
        layout.addWidget(outputLabel)
        layout.addWidget(self.output)

    def updatePorts(self):
        self.output.clear()
        for p in self.gui.song.outputsMidiPorts:
            self.output.addItem(p.name)
        self.output.setCurrentIndex(self.output.findText(self.parent.clip.output))

    def onNameChanged(self, name):
        self.parent.clip.name = name
        self.parent.cell.clip_name.setText(name)

    def onMidiChannelChanged(self, channel):
        self.parent.clip.channel = channel - 1
        self.parent.clip.computeEvents()

    def onLengthChanged(self, length):
        # Set new length in the clip
        self.parent.clip.length = length
        # Re-generate piano grid widget
        self.parent.updateUI()
    
    def onQuantizeChanged(self, quantize):
        #tick_round_counts = [1, 24/2, 24/4, 24/3, 24/6, 24/12]
        tick_round = int(24/QUANTIZE_DIVISERS[quantize])
        for note in self.parent.clip.notes:
            note.start_tick = round(note.start_tick / tick_round) * tick_round
            note.length = round(note.length / tick_round) * tick_round
        grid: QGraphicsScene = self.parent.piano_grid.scene
        for item in grid.items():
            if isinstance(item, MidiNoteItem):
                item.reDraw()
        self.parent.clip.quantize = QUANTIZE_DIVISERS[quantize]
    
    def onMuteGroupChanged(self, index):
        self.parent.clip.mute_group = index

    def onOutputChanged(self, i):
        self.parent.clip.output = self.output.itemText(i)

    # Return Quantization step in tick
    def getTickSnap(self):
        return int(24/QUANTIZE_DIVISERS[self.quantize.currentIndex()])