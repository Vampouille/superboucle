from time import time_ns
from math import pi
from PyQt5.QtWidgets import (
    QDialog,
)
from PyQt5.QtCore import QTimer, QRect
from superboucle.tape_manager_ui import Ui_Dialog
from superboucle.tape_visual import LoopPathWidget
from superboucle.tape_speed_visual import TapeSpeedVisualWidget
from superboucle.tape import HardwareTapeLoop, NoDeviceConnected
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

        self.tape_speed_visual = TapeSpeedVisualWidget(self)
        self.tape_speed_visual.setGeometry(QRect(220, 300, 600, 50))

        self.startButton.clicked.connect(self.onStart)
        self.stopButton.clicked.connect(self.onStop)

        self.tape: HardwareTapeLoop = self.gui.hardwaretapeloop
        self.tape_size = self.tape.getTapeSizeIncm()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.updateDisplay)
        self.refresh_timer.start(50)  # Update every 50 ms
        self.last_pos = None
        self.last_time = None

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
    
    def onStop(self):
        self.started = False

    def updateDisplay(self):
        try:
            self.tape_visual.set_position(self.tape.getRelativePositionIncm() / self.tape_size)
            cur_pos = self.tape.getAbsolutePositionIncm() 
            cur_time = time_ns()
            if self.last_pos is not None:
                # speed in cm per nano second
                speed = (cur_pos - self.last_pos) / (cur_time - self.last_time)
                speed *= 1e9
                speed_text = "%.2f" % speed
                self.speedValue.setText(f"{speed_text} cm/s")
                self.tape_speed_visual.set_speed(speed)
            self.last_pos = cur_pos
            self.last_time = cur_time
        except NoDeviceConnected:
            pass