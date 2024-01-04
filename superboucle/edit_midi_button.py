from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QSpinBox, QComboBox, QAbstractSpinBox



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
        self.midiChannelLabel = QLabel(self)
        self.midiChannelLabel.setGeometry(QRect(10, 10, 112, 25))
        self.midiChannelLabel.setFont(font)
        self.midiChannelLabel.setStyleSheet(css)
        self.midiChannelLabel.setAlignment(Qt.AlignCenter)
        self.midiChannelLabel.setObjectName("midiChannelLabel")
        self.midiChannelLabel.setText("MIDI Channel")
        self.midiChannel = QSpinBox(self)
        self.midiChannel.setGeometry(QRect(130, 10, 42, 26))
        self.midiChannel.setFont(font)
        self.midiChannel.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.midiChannel.setMinimum(1)
        self.midiChannel.setMaximum(16)
        self.midiChannel.setObjectName("midiChannel")
        self.midiChannel.setValue(self.parent.clip.channel + 1)
        self.midiChannel.valueChanged.connect(self.onMidiChannelChange)

        # Quantize
        self.quantizeLabel = QLabel(self)
        self.quantizeLabel.setGeometry(QRect(190, 10, 92, 25))
        self.quantizeLabel.setFont(font)
        self.quantizeLabel.setStyleSheet(css)
        self.quantizeLabel.setAlignment(Qt.AlignCenter)
        self.quantizeLabel.setObjectName("quantizeLabel")
        self.quantizeLabel.setText("Quantize")
        self.quantize = QComboBox(self)
        self.quantize.setGeometry(QRect(280, 10, 72, 25))
        self.quantize.setFont(font)
        self.quantize.setCurrentText("")
        self.quantize.setObjectName("quantize")
        self.quantize.addItem("Off")
        self.quantize.addItem("1/4")
        self.quantize.addItem("1/2")
        self.quantize.addItem("1/3")
        self.quantize.addItem("1/6")
        self.quantize.addItem("1/12")

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