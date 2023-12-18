# 5 pixel per tick
# 24*5=120 pixel per beat
# Quantize:
# 1/4: 24/4: quantize on 6 tick : 30 pixel
# 1/2: 24/2: quantize on 12 tick: 60 pixel
# 1/3: 24/3: quantize on 8 tick : 40 pixel
# 1/6: 24/6: quantize on 4 tick : 20 pixel


from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt, QSize, QRect
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QDialog, QVBoxLayout, QPushButton, QScrollArea, QWidget, QSizePolicy, QLabel, QSpinBox, QComboBox, QAbstractSpinBox


class EditMidiDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)

        self.view = QGraphicsView(self.scene)
        self.view.setSceneRect(0, 0, 1000, 1300)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(self.view)
        self.scroll_area.setWidgetResizable(True)  # La QScrollArea s'ajustera à la taille de son contenu

        layout = QVBoxLayout(self)
        layout.addWidget(self.generateButton())
        layout.addWidget(self.scroll_area)
        layout.setStretch(1, 1)

        # Définir la taille minimale de la QScrollArea sur la taille minimale de la QGraphicsView
        #self.scroll_area.setMinimumSize(int(self.view.sceneRect().width()), int(self.view.sceneRect().height()))

        self.setWindowTitle("Edit MIDI Notes")
        self.setGeometry(100, 100, 800, 600)

        self.createPianoRoll()
        self.show()


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
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        #widget.setSizePolicy(sizePolicy)
        widget.setMinimumSize(QSize(530, 35))
        widget.setObjectName("widget")
        self.beat_diviser = QSpinBox(widget)
        self.beat_diviser.setGeometry(QRect(430, 10, 71, 21))
        self.beat_diviser.setStyleSheet("QSpinBox::up-button { width: 40px; }\n"
"QSpinBox::down-button { width: 40px; }\n"
"QSpinBox { border : 0px; border-radius: 2px}")
        self.beat_diviser.setMinimum(1)
        self.beat_diviser.setMaximum(999)
        self.beat_diviser.setObjectName("beat_diviser")
        self.comboBox = QComboBox(widget)
        self.comboBox.setGeometry(QRect(280, 10, 72, 25))
        self.comboBox.setFont(font)
        self.comboBox.setCurrentText("")
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("Off")
        self.comboBox.addItem("1/4")
        self.comboBox.addItem("1/2")
        self.comboBox.addItem("1/3")
        self.comboBox.addItem("1/6")
        self.label_13 = QLabel(widget)
        self.label_13.setGeometry(QRect(190, 10, 92, 25))
        self.label_13.setFont(font)
        self.label_13.setStyleSheet(css)
        self.label_13.setAlignment(Qt.AlignCenter)
        self.label_13.setObjectName("label_13")
        self.label_13.setText("Quantize")
        self.label_14 = QLabel(widget)
        self.label_14.setGeometry(QRect(360, 10, 61, 25))
        self.label_14.setFont(font)
        self.label_14.setStyleSheet(css)
        self.label_14.setAlignment(Qt.AlignCenter)
        self.label_14.setObjectName("label_14")
        self.label_14.setText("Length")
        self.label_12 = QLabel(widget)
        self.label_12.setGeometry(QRect(20, 10, 92, 25))
        self.label_12.setFont(font)
        self.label_12.setStyleSheet(css)
        self.label_12.setAlignment(Qt.AlignCenter)
        self.label_12.setObjectName("label_12")
        self.label_12.setText("MIDI Channel")
        self.spinBox = QSpinBox(widget)
        self.spinBox.setGeometry(QRect(130, 10, 42, 26))
        self.spinBox.setFont(font)
        self.spinBox.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(16)
        self.spinBox.setObjectName("spinBox")
        return widget


    def createPianoRoll(self):
        # Ajout du clavier de piano sur le côté gauche
        keyboard_width = 50
        keyboard_height = self.view.sceneRect().height()
        keyboard_item = QGraphicsRectItem(0, 0, keyboard_width, keyboard_height)
        keyboard_item.setBrush(Qt.lightGray)
        self.scene.addItem(keyboard_item)

        # Ajout des lignes verticales représentant les beats
        beats = 16
        beat_width = self.view.sceneRect().width() / beats

        for beat in range(beats + 1):
            x = beat * beat_width
            line = self.scene.addLine(x, 0, x, keyboard_height)
            line.setPen(Qt.black)

        notes = 88
        # Hauteur d'une note
        note_height = self.view.sceneRect().height() / notes

        for note in range(12, 12 + 88):  # Start from C0 (MIDI number 12)
            y = (note - 12) * note_height  # Adjustment to compensate for the offset
            note_item = QGraphicsRectItem(0, y, self.view.sceneRect().width(), note_height)

            # Set the color based on the note (black or white)
            if (note + 9) % 12 in {1, 4, 6, 9, 11}:  # Indices of black keys
                note_item.setBrush(QColor(200, 200, 200))  # Light gray for black keys
            else:
                note_item.setBrush(Qt.white)  # White for white keys

            self.scene.addItem(note_item)

    def resizeEvent(self, event):
        print("Dialog Geometry:", self.geometry())
        #print("Vertical Layout Geometry:", self.verticalLayout.geometry())
        print("Scroll Area Geometry:", self.scroll_area.geometry())
