from PyQt5.QtWidgets import QDialog, QWidget

from PyQt5.QtCore import pyqtSignal
import struct
from queue import Queue, Empty
from learn_cell_ui import Ui_LearnCell
from learn_ui import Ui_Dialog
import re

_init_cmd_regexp = re.compile("^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$")


class LearnCell(QWidget, Ui_LearnCell):

    def __init__(self, parent):
        super(LearnCell, self).__init__(parent)
        self.setupUi(self)


class LearnDialog(QDialog, Ui_Dialog):

    NOTEON = 0x9
    NOTEOFF = 0x8
    MIDICTRL = 11
    NEW_CELL_STYLE = ("#cell_frame {border: 0px; "
                      "border-radius: 5px; "
                      "background-color: rgb(217, 217, 217);}")
    NEW_CELL_STYLE_ROUND = ("#cell_frame {border: 0px; "
                            "border-radius: 20px; "
                            "background-color: rgb(217, 217, 217);}")

    NOTE_NAME = ['C', 'C#',
                 'D', 'D#',
                 'E',
                 'F', 'F#',
                 'G', 'G#',
                 'A', 'A#',
                 'B']

    # send_midi_to values :
    START_STOP = 0
    MASTER_VOLUME_CTRL = 1
    CTRLS = 2
    BLOCK_BUTTONS = 3

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
        self.knownCtrl = set()
        self.knownBtn = set()
        self.block_bts_list = []
        self.send_midi_to = None
        self.updateUi.connect(self.update)
        self.setupUi(self)
        self.accepted.connect(self.onSave)
        self.firstLine.clicked.connect(self.onFirstLineClicked)
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
        self.green_vel.valueChanged.connect(self.onGreen)
        self.blink_green_vel.valueChanged.connect(self.onBlinkGreen)
        self.red_vel.valueChanged.connect(self.onRed)
        self.blink_red_vel.valueChanged.connect(self.onBlinkRed)
        self.show()

    def onFirstLineClicked(self):
        self.send_midi_to = self.START_STOP

        if self.current_line is None:
            self.current_line = 0
            self.firstLine.setText("Add Next line")
        else:
            self.current_line += 1

        self.current_line_pitch = []
        self.pitch_matrix.append(self.current_line_pitch)
        self.firstLine.setEnabled(False)
        self.current_row = 0
        cell = LearnCell(self)
        self.gridLayout.addWidget(cell,
                                  self.current_line,
                                  self.current_row)

    def onMasterVolumeCtrl(self):
        self.send_midi_to = self.MASTER_VOLUME_CTRL

    def onCtrls(self):
        self.send_midi_to = self.CTRLS

    def onBlockBts(self):
        self.send_midi_to = self.BLOCK_BUTTONS

    def onStopClicked(self):
        self.send_midi_to = None

    def onGreen(self):
        self.lightAllCell(self.green_vel.value())

    def onBlinkGreen(self):
        self.lightAllCell(self.blink_green_vel.value())

    def onRed(self):
        self.lightAllCell(self.red_vel.value())

    def onBlinkRed(self):
        self.lightAllCell(self.blink_red_vel.value())

    def lightAllCell(self, velocity):
        for line in self.pitch_matrix:
            for chnote in line:
                channel = chnote >> 8
                note = chnote & 0x7F
                self.gui.queue_out.put((144 + channel,
                                        note,
                                        velocity))

    def update(self):
        try:
            while True:
                data = self.queue.get(block=False)
                if len(data) == 3:
                    status, pitch, vel = struct.unpack('3B', data)
                    self.processNote(status, pitch, vel)
        except Empty:
            pass

    def processNote(self, status, pitch, velocity):
        # process controller
        channel = status & 0xF
        msg_type = status >> 4
        chnote = (channel << 8) + pitch

        if self.send_midi_to == self.MASTER_VOLUME_CTRL:
            if msg_type == self.MIDICTRL:
                if chnote not in self.knownCtrl:
                    self.mapping['master_volume_ctrl'] = chnote
                    self.label_master_volume_ctrl.setText(("Channel %s "
                                                           "Controller %s")
                                                          % (channel + 1,
                                                             pitch))
                    self.knownCtrl.add(chnote)
                    self.send_midi_to = None

        elif self.send_midi_to == self.CTRLS:
            if msg_type == self.MIDICTRL:
                if chnote not in self.knownCtrl:
                    cell = LearnCell(self)
                    cell.label.setText("Ch %s\n%s"
                                       % (channel + 1, pitch))
                    cell.setStyleSheet(self.NEW_CELL_STYLE_ROUND)
                    self.ctrlsHorizontalLayout.addWidget(cell)
                    self.mapping['ctrls'].append(chnote)
                    self.knownCtrl.add(chnote)

        # then process note off
        elif msg_type == self.NOTEON and chnote not in self.knownBtn:
            if self.send_midi_to == self.BLOCK_BUTTONS:
                cell = LearnCell(self)
                cell.label.setText("Ch %s\n%s"
                                   % (channel + 1,
                                      self.displayNote(pitch)))
                cell.setStyleSheet(self.NEW_CELL_STYLE)
                self.btsHorizontalLayout.addWidget(cell)
                self.mapping['block_buttons'].append(chnote)

            elif self.send_midi_to == self.START_STOP:
                self.current_line_pitch.append(chnote)
                cell = LearnCell(self)
                cell.label.setText("Ch %s\n%s"
                                   % (channel + 1,
                                      self.displayNote(pitch)))
                cell.setStyleSheet(self.NEW_CELL_STYLE)
                self.gridLayout.addWidget(cell,
                                          self.current_line,
                                          self.current_row)
                self.current_row += 1
                self.firstLine.setEnabled(True)

            self.knownBtn.add(chnote)

    def onSave(self):
        self.mapping['start_stop'] = self.pitch_matrix
        self.mapping['name'] = str(self.name.text())
        self.mapping['green_vel'] = int(self.green_vel.value())
        self.mapping['blink_green_vel'] = int(self.blink_green_vel.value())
        self.mapping['red_vel'] = int(self.red_vel.value())
        self.mapping['blink_red_vel'] = int(self.blink_red_vel.value())
        self.mapping['init_command'] = (
            self.parseInitCommand(str(self.init_command.toPlainText())))
        self.gui.is_add_device_mode = False
        self.gui.addDevice(self.mapping)
        self.gui.redraw()

    def displayNote(self, note_dec):
        octave, note = divmod(note_dec, 12)
        octave += 1
        note_str = self.NOTE_NAME[note]
        return note_str[:1] + str(octave) + note_str[1:]

    def parseInitCommand(self, raw_str):
        init_commands = []
        for raw_line in raw_str.split("\n"):
            matches = _init_cmd_regexp.match(raw_line)
            if matches:
                byte1 = int(matches.group(1))
                byte2 = int(matches.group(2))
                byte3 = int(matches.group(3))
                if not 0 <= byte1 < 256:
                    raise Exception("byte 1 Out of range")
                if not 0 <= byte2 < 256:
                    raise Exception("byte 2 Out of range")
                if not 0 <= byte3 < 256:
                    raise Exception("byte 3 Out of range")
                init_commands.append((byte1, byte2, byte3))
            else:
                print("Not matching")
        return init_commands
