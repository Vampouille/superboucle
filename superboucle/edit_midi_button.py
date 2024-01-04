from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QSpinBox, QComboBox, QAbstractSpinBox, QGraphicsScene, QToolButton, QHBoxLayout
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
        self.quantize.addItem("Off")
        self.quantize.addItem("1/2")
        self.quantize.addItem("1/4")
        self.quantize.addItem("1/3")
        self.quantize.addItem("1/6")
        self.quantize.addItem("1/12")
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

        # Select Tool
        select_icon = QIcon()
        select_icon.addPixmap(QPixmap(":/icons/icons/select-delete-icon-16.png"), QIcon.Normal, QIcon.Off)
        self.select_tool = QToolButton()
        self.select_tool.setIcon(select_icon)
        self.select_tool.setIconSize(QSize(32, 16))
        self.select_tool.setToolTip('This tool allow to select note for velocity edit and deletion with \'Del\' key')
        self.select_tool.clicked.connect(lambda: self.buttonClicked(self.select_tool))
        layout.addWidget(self.select_tool)

        # Edit tool
        edit_icon = QIcon()
        edit_icon.addPixmap(QPixmap(":/icons/icons/edit-icon-16.png"), QIcon.Normal, QIcon.Off)
        self.edit_tool = QToolButton()
        self.edit_tool.setIcon(edit_icon)
        self.edit_tool.setIconSize(QSize(16, 16))
        self.edit_tool.setToolTip('This tool allow note edition and creation')
        self.edit_tool.clicked.connect(lambda: self.buttonClicked(self.edit_tool))
        self.buttonClicked(self.edit_tool)
        layout.addWidget(self.edit_tool)

    def buttonClicked(self, clicked_button):
        for tool in [self.select_tool, self.edit_tool]:
            tool.setCheckable(True)
            if tool is clicked_button:
                tool.setChecked(True)
                self.setButtonBackground(tool, 'rgb(247, 42, 151)')
            else:
                tool.setChecked(False)
                tool.setStyleSheet('')

    def setButtonBackground(self, button, color):
        button.setStyleSheet(f'''
            QToolButton {{
                background-color: {color};
            }}
            QToolButton::menu-indicator {{
                background-color: window; 
            }}
        ''')

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
    
    def getTickSnap(self):
        self.quantize.currentIndex()
        tick_round_counts = [1, 24/2, 24/4, 24/3, 24/6, 24/12]
        return int(tick_round_counts[self.quantize.currentIndex()])
