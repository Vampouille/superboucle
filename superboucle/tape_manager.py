from PyQt5.QtWidgets import (
    QDialog,
    QListWidgetItem,
    QAbstractItemView,
    QTableWidgetItem,
    QInputDialog,
)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt, QTimer, QRect
from superboucle.tape_manager_ui import Ui_Dialog
from superboucle.tape_visual import LoopPathWidget
from superboucle.song import verify_ext

TOOLTIP_STYLE = """
    QToolTip {
        background-color: rgb(6, 147, 152);
        padding: 5px;
    }
"""
class TapeManager(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(TapeManager, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.setWindowTitle("Magnetic Tape Manager")

        self.tape_visual = LoopPathWidget(self, "tape_path.svg")
        self.tape_visual.setGeometry(QRect(220, 90, 600, 200))

        self.startButton.clicked.connect(self.onStart)
        self.stopButton.clicked.connect(self.onStop)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updatePosition)
        self.timer.start(50)  # Update every 50 ms

        self.started = False
        self.current_position = 0

        #self.midiPorts.setStyleSheet(TOOLTIP_STYLE)
        #self.midiPorts.itemClicked.connect(self.onEditMidiRegexp)
        #self.addAudioPort.clicked.connect(self.onAddAudioPort)
        #self.midiControlInput.textChanged.connect(self.onChangedMidiControlInput)
        #self.gui.superboucleConnectionChangeSignal.connect(self.updateStatus)

        self.update()
        self.show()

    def onStart(self):
        self.started = True
        self.timer.start()
    
    def onStop(self):
        self.started = False
        self.timer.stop()

    def updatePosition(self):
        if self.started:
            self.current_position += 1
            self.tape_visual.set_position(self.current_position / 100)