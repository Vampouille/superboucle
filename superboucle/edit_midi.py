# 5 pixel per tick
# 24*5=120 pixel per beat
# Quantize:
# 1/4: 24/4: quantize on 6 tick : 30 pixel
# 1/2: 24/2: quantize on 12 tick: 60 pixel
# 1/3: 24/3: quantize on 8 tick : 40 pixel
# 1/6: 24/6: quantize on 4 tick : 20 pixel


from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QColor
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QPushButton, QGraphicsRectItem, QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QScrollBar, QWidget, QLabel, QSpinBox, QComboBox, QAbstractSpinBox
from superboucle.piano_grid import PianoGridWidget
from superboucle.piano_keyboard import PianoKeyboardWidget


class CustomScrollBar(QScrollBar):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)

class EditMidiDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)

        # Root Layout with:
        # * button
        # * body 
        root_layout = QVBoxLayout(self)
        root_layout.addWidget(self.generateButton())

        # Body Widget:
        # * piano keyboard
        # * piano grid
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)

        # Note Grid
        self.g_scroll_area = QScrollArea(self)
        self.g_scroll_area.setWidget(PianoGridWidget(self.g_scroll_area, 1000, 1344))
        self.g_scroll_area.setWidgetResizable(True)
        self.g_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Piano Keyboard
        self.p_scroll_area = QScrollArea(self)
        self.p_scroll_area.setWidget(PianoKeyboardWidget(self.p_scroll_area, 68, 1344))
        self.p_scroll_area.setWidgetResizable(True)
        self.p_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Synchronize scroll area
        self.g_scroll_area.verticalScrollBar().valueChanged.connect(self.syncScrollArea)
        self.p_scroll_area.verticalScrollBar().valueChanged.connect(self.syncScrollArea)
        self.g_scroll_area.horizontalScrollBar().valueChanged.connect(self.syncScrollArea)
        self.p_scroll_area.horizontalScrollBar().valueChanged.connect(self.syncScrollArea)

        # Insert widgets in the dialog
        body_layout.addWidget(self.p_scroll_area)
        body_layout.addWidget(self.g_scroll_area)
        body_layout.setStretch(1, 1)
        root_layout.addWidget(body_widget)
        root_layout.setStretch(1, 1)

        self.setWindowTitle("Edit MIDI Notes")
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def syncScrollArea(self, value):
        sender = self.sender()
        print("Sender:", sender)
        print("Piano Scroll Value: %s/%s", (self.p_scroll_area.verticalScrollBar().value(), self.p_scroll_area.horizontalScrollBar().value()))
        print("Grid Scroll Value: %s/%s", (self.g_scroll_area.verticalScrollBar().value(), self.g_scroll_area.horizontalScrollBar().value()))

        if sender == self.p_scroll_area.verticalScrollBar():
            self.g_scroll_area.verticalScrollBar().setValue(value)
        elif sender == self.g_scroll_area.verticalScrollBar():
            self.p_scroll_area.verticalScrollBar().setValue(value)

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

        return widget

    def resizeEvent(self, event):
        print("Dialog Geometry:", self.geometry())
        #print("Vertical Layout Geometry:", self.verticalLayout.geometry())
        print("Piano Scroll Area Geometry:", self.p_scroll_area.geometry())
        print("Grid Scroll Area Geometry:", self.g_scroll_area.geometry())
