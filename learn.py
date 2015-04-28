from PyQt5.QtWidgets import (QDialog,
                             QDial,
                             QWidget)

from PyQt5.QtCore import pyqtSignal
import struct
from queue import Queue, Empty
from learn_cell_ui import Ui_LearnCell
from learn_ui import Ui_Dialog


class LearnCell(QWidget, Ui_LearnCell):

    def __init__(self, parent):
        super(LearnCell, self).__init__(parent)
        self.setupUi(self)


class LearnDialog(QDialog, Ui_Dialog):

    NOTEON = 0x9
    NOTEOFF = 0x8
    NEW_CELL_STYLE = ("border: 0px; "
                      "border-radius: 10px; "
                      "background-color: rgb(217, 217, 217);")

    # send_midi_to values :
    START_STOP = 0
    MASTER_VOLUME = 1
    CLIP_VOLUME = 2
    BEAT_DIVISER = 3
    BEAT_OFFSET = 4
    MASTER_VOLUME_CTRL = 5
    CTRLS = 6
    BLOCK_BUTTONS = 7

    updateUi = pyqtSignal()

    def __init__(self, parent):
        super(LearnDialog, self).__init__(parent)
        self.gui = parent
        self.queue = Queue()
        self.mapping = {'block_buttons': [],
                        'ctrls': []}
        self.current_line = None
        self.current_row = None
        self.current_line_pitch = []
        self.pitch_matrix = []
        self.ctrls_list = []
        self.block_bts_list = []
        self.send_midi_to = None
        self.updateUi.connect(self.update)
        self.setupUi(self)
        self.accepted.connect(self.onSave)
        self.firstLine.clicked.connect(self.onFirstLineClicked)
        self.learn_master_volume.clicked.connect(self.onMasterVolumeClicked)
        self.learn_clip_volume.clicked.connect(self.onClipVolumeClicked)
        self.learn_beat_diviser.clicked.connect(self.onBeatDiviserClicked)
        self.learn_beat_offset.clicked.connect(self.onBeatOffsetClicked)
        self.learn_master_volume_ctrl.clicked.connect(self.onMasterVolumeCtrl)
        self.learn_ctrls.clicked.connect(self.onCtrls)
        self.learn_block_bts.clicked.connect(self.onBlockBts)
        self.stop1.clicked.connect(self.onStopClicked)
        self.stop2.clicked.connect(self.onStopClicked)
        self.stop3.clicked.connect(self.onStopClicked)
        self.learn_green.clicked.connect(self.onGreen)
        self.learn_blink_green.clicked.connect(self.onBlinkGreen)
        self.learn_red.clicked.connect(self.onRed)
        self.learn_blink_red.clicked.connect(self.onBlinkRed)
        self.green_ch.valueChanged.connect(self.onGreen)
        self.green_vel.valueChanged.connect(self.onGreen)
        self.green_has2.toggled.connect(self.onGreen2Toogle)
        self.green_ch2.valueChanged.connect(self.onGreen)
        self.green_vel2.valueChanged.connect(self.onGreen)
        self.blink_green_ch.valueChanged.connect(self.onBlinkGreen)
        self.blink_green_vel.valueChanged.connect(self.onBlinkGreen)
        self.blink_green_has2.toggled.connect(self.onBlinkGreen2Toogle)
        self.blink_green_ch2.valueChanged.connect(self.onBlinkGreen)
        self.blink_green_vel2.valueChanged.connect(self.onBlinkGreen)
        self.red_ch.valueChanged.connect(self.onRed)
        self.red_vel.valueChanged.connect(self.onRed)
        self.red_has2.toggled.connect(self.onRed2Toogle)
        self.red_ch2.valueChanged.connect(self.onRed)
        self.red_vel2.valueChanged.connect(self.onRed)
        self.blink_red_ch.valueChanged.connect(self.onBlinkRed)
        self.blink_red_vel.valueChanged.connect(self.onBlinkRed)
        self.blink_red_has2.toggled.connect(self.onBlinkRed2Toogle)
        self.blink_red_ch2.valueChanged.connect(self.onBlinkRed)
        self.blink_red_vel2.valueChanged.connect(self.onBlinkRed)
        self.show()

    def onFirstLineClicked(self):
        self.send_midi_to = self.START_STOP

        if self.current_line is None:
            self.current_line = 0
            self.firstLine.setText("Add Next line")
        else:
            self.pitch_matrix.append(self.current_line_pitch)
            self.current_line += 1

        print("Clicked")
        self.firstLine.setEnabled(False)
        self.current_row = 0
        self.current_line_pitch = []
        cell = LearnCell(self)
        self.gridLayout.addWidget(cell,
                                  self.current_line,
                                  self.current_row)

    def onMasterVolumeClicked(self):
        self.send_midi_to = self.MASTER_VOLUME

    def onClipVolumeClicked(self):
        self.send_midi_to = self.CLIP_VOLUME

    def onBeatDiviserClicked(self):
        self.send_midi_to = self.BEAT_DIVISER

    def onBeatOffsetClicked(self):
        self.send_midi_to = self.BEAT_OFFSET

    def onMasterVolumeCtrl(self):
        self.send_midi_to = self.MASTER_VOLUME_CTRL

    def onCtrls(self):
        self.send_midi_to = self.CTRLS

    def onBlockBts(self):
        self.send_midi_to = self.BLOCK_BUTTONS

    def onStopClicked(self):
        self.send_midi_to = None

    def onGreen(self):
        pass

    def onBlinkGreen(self):
        pass

    def onRed(self):
        pass

    def onBlinkRed(self):
        pass

    def onGreen2Toogle(self):
        pass

    def onBlinkGreen2Toogle(self):
        pass

    def onRed2Toogle(self):
        pass

    def onBlinkRed2Toogle(self):
        pass

    def update(self):
        try:
            while True:
                data = self.queue.get(block=False)
                if len(data) == 3:
                    status, pitch, vel = struct.unpack('3B', data)
                    self.processNote(status, pitch, vel)
                    print(pitch)
        except Empty:
            pass

    def processNote(self, status, pitch, velocity):
        # process controller
        if self.send_midi_to == self.MASTER_VOLUME_CTRL:
            self.mapping['master_volume_ctrl'] = (status, pitch, velocity)
            self.label_master_volume_ctrl.setText("Midi note On {}".
                                                  format(pitch))
            self.send_midi_to = None
        elif self.send_midi_to == self.CTRLS:
            self.addCtrl(status, pitch, velocity)
        elif status >> 4 == self.NOTEOFF:  # then process note off
            if self.send_midi_to == self.BLOCK_BUTTONS:
                self.addBlockBtn(pitch)
            elif self.send_midi_to == self.START_STOP:
                print("New note : {0} at {1} x {2}".
                      format(pitch, self.current_line, self.current_row))
                self.current_line_pitch.append(pitch)
                cell = LearnCell(self)
                cell.setStyleSheet(self.NEW_CELL_STYLE)
                self.gridLayout.addWidget(cell,
                                          self.current_line,
                                          self.current_row)
                self.current_row += 1
                self.firstLine.setEnabled(True)
            else:
                if self.send_midi_to == self.MASTER_VOLUME:
                    self.mapping['master_volume'] = pitch
                    self.label_master_volume.setText("Midi note On {}".
                                                     format(pitch))
                elif self.send_midi_to == self.CLIP_VOLUME:
                    self.mapping['clip_volume'] = pitch
                    self.label_clip_volume.setText("Midi note On {}".
                                                   format(pitch))
                elif self.send_midi_to == self.BEAT_DIVISER:
                    self.mapping['beat_diviser'] = pitch
                    self.label_beat_diviser.setText("Midi note On {}".
                                                    format(pitch))
                elif self.send_midi_to == self.BEAT_OFFSET:
                    self.mapping['beat_offset'] = pitch
                    self.label_beat_offset.setText("Midi note On {}".
                                                   format(pitch))
                self.send_midi_to = None

    def addCtrl(self, status, note, velocity):
        self.mapping['ctrls'].append((status, note, velocity))
        self.ctrlsHorizontalLayout.addWidget(QDial())

    def addBlockBtn(self, note):
        self.mapping['block_buttons'].append(note)
        cell = LearnCell(self)
        cell.setStyleSheet(self.NEW_CELL_STYLE)
        self.btsHorizontalLayout.addWidget(cell)

    def onSave(self):
        self.pitch_matrix.append(self.current_line_pitch)
        self.mapping['start_stop'] = self.pitch_matrix
        self.mapping['name'] = str(self.name.text())
        print(self.mapping)
        self.gui.is_add_device_mode = False
        self.gui.addDevice(self.mapping)
        self.gui.redraw()
