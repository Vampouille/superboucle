from PyQt5.QtWidgets import QDialog, QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
import struct
from copy import deepcopy
from queue import Queue, Empty
from learn_cell_ui import Ui_LearnCell
from learn_ui import Ui_Dialog
from device import Device
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
    PLAY_BTN = 4
    PAUSE_BTN = 5
    REWIND_BTN = 6
    GOTO_BTN = 7
    RECORD_BTN = 8
    SCENES_BTN = 9

    updateUi = pyqtSignal()

    def __init__(self, parent, callback, device=None):
        super(LearnDialog, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.callback = callback
        self.queue = Queue()
        if device is None:
            self.original_device = Device()
        else:
            self.original_device = device
            self.setWindowTitle("Edit %s" % device.name)

        # perform deep copy in order to keep original values if cancel is
        # clicked
        self.device = Device(deepcopy(self.original_device.mapping))
        self.current_line = None
        self.current_row = None
        self.current_line_pitch = []
        self.knownCtrl = set()
        self.knownBtn = set()
        self.block_bts_list = []
        self.send_midi_to = None
        self.updateUi.connect(self.update)

        # set current device values
        self.name.setText(self.device.name)
        self.black_vel.setValue(self.device.black_vel)
        self.green_vel.setValue(self.device.green_vel)
        self.blink_green_vel.setValue(self.device.blink_green_vel)
        self.red_vel.setValue(self.device.red_vel)
        self.blink_red_vel.setValue(self.device.blink_red_vel)
        self.amber_vel.setValue(self.device.amber_vel)
        self.blink_amber_vel.setValue(self.device.blink_amber_vel)
        if self.device.master_volume_ctrl:
            (self.label_master_volume_ctrl.setText(
                self.displayCtrl(self.device.master_volume_ctrl)))
        if self.device.play_btn:
            self.playLabel.setText(self.displayBtn(self.device.play_btn))
        if self.device.pause_btn:
            self.pauseLabel.setText(self.displayBtn(self.device.pause_btn))
        if self.device.rewind_btn:
            self.rewindLabel.setText(self.displayBtn(self.device.rewind_btn))
        if self.device.goto_btn:
            self.gotoLabel.setText(self.displayBtn(self.device.goto_btn))
        if self.device.record_btn:
            self.recordLabel.setText(self.displayBtn(self.device.record_btn))
        (self.init_command
         .setText("\n".join([", ".join([str(num)
                                        for num in init_cmd])
                             for init_cmd in self.device.init_command])))
        for vol_btn in self.device.scene_buttons:
            (msg_type, channel, pitch, velocity) = vol_btn
            cell = LearnCell(self)
            cell.label.setText("Ch %s\n%s"
                               % (channel + 1,
                                  self.displayNote(pitch)))
            cell.setStyleSheet(self.NEW_CELL_STYLE)
            self.scenesHorizontalLayout.addWidget(cell)
        for vol_btn in self.device.block_buttons:
            (msg_type, channel, pitch, velocity) = vol_btn
            cell = LearnCell(self)
            cell.label.setText("Ch %s\n%s"
                               % (channel + 1,
                                  self.displayNote(pitch)))
            cell.setStyleSheet(self.NEW_CELL_STYLE)
            self.btsHorizontalLayout.addWidget(cell)
        for vol_ctrl in self.device.ctrls:
            (msg_type, channel, pitch) = vol_ctrl
            cell = LearnCell(self)
            cell.label.setText("Ch %s\n%s"
                               % (channel + 1, pitch))
            cell.setStyleSheet(self.NEW_CELL_STYLE_ROUND)
            self.ctrlsHorizontalLayout.addWidget(cell)
        for line in self.device.start_stop:
            if self.current_line is None:
                self.current_line = 0
                self.firstLine.setText("Add Next line")
            else:
                self.current_line += 1
            self.current_row = 0

            for btn_key in line:
                (msg_type, channel, pitch, velocity) = btn_key
                cell = LearnCell(self)
                cell.label.setText("Ch %s\n%s"
                                   % (channel + 1,
                                      self.displayNote(pitch)))
                cell.setStyleSheet(self.NEW_CELL_STYLE)
                self.gridLayout.addWidget(cell,
                                          self.current_line,
                                          self.current_row)
                self.current_row += 1

        # connect signals
        self.accepted.connect(self.onSave)
        self.firstLine.clicked.connect(self.onFirstLineClicked)
        self.learn_master_volume_ctrl.clicked.connect(self.onMasterVolumeCtrl)
        self.playButton.clicked.connect(self.onPlayButton)
        self.pauseButton.clicked.connect(self.onPauseButton)
        self.rewindButton.clicked.connect(self.onRewindButton)
        self.gotoButton.clicked.connect(self.onGotoButton)
        self.recordButton.clicked.connect(self.onRecordButton)
        self.sendInitButton.clicked.connect(self.onSendInit)
        self.learn_ctrls.clicked.connect(self.onCtrls)
        self.learn_block_bts.clicked.connect(self.onBlockBts)
        self.learn_scenes.clicked.connect(self.onScenesButton)
        self.stop1.clicked.connect(self.onStopClicked)
        self.stop2.clicked.connect(self.onStopClicked)
        self.stop3.clicked.connect(self.onStopClicked)
        self.stop4.clicked.connect(self.onStopClicked)
        self.learn_black.clicked.connect(self.onBlack)
        self.learn_green.clicked.connect(self.onGreen)
        self.learn_blink_green.clicked.connect(self.onBlinkGreen)
        self.learn_red.clicked.connect(self.onRed)
        self.learn_blink_red.clicked.connect(self.onBlinkRed)
        self.learn_amber.clicked.connect(self.onAmber)
        self.learn_blink_amber.clicked.connect(self.onBlinkAmber)
        self.black_vel.valueChanged.connect(self.onBlack)
        self.green_vel.valueChanged.connect(self.onGreen)
        self.blink_green_vel.valueChanged.connect(self.onBlinkGreen)
        self.red_vel.valueChanged.connect(self.onRed)
        self.blink_red_vel.valueChanged.connect(self.onBlinkRed)
        self.amber_vel.valueChanged.connect(self.onAmber)
        self.blink_amber_vel.valueChanged.connect(self.onBlinkAmber)
        self.show()

    def onFirstLineClicked(self):
        self.send_midi_to = self.START_STOP

        if self.current_line is None:
            self.current_line = 0
            self.firstLine.setText("Add Next line")
        else:
            self.current_line += 1

        self.current_line_pitch = []
        self.device.start_stop.append(self.current_line_pitch)
        self.firstLine.setEnabled(False)
        self.current_row = 0
        cell = LearnCell(self)
        self.gridLayout.addWidget(cell,
                                  self.current_line,
                                  self.current_row)

    def onMasterVolumeCtrl(self):
        self.send_midi_to = self.MASTER_VOLUME_CTRL

    def onPlayButton(self):
        self.send_midi_to = self.PLAY_BTN

    def onPauseButton(self):
        self.send_midi_to = self.PAUSE_BTN

    def onRewindButton(self):
        self.send_midi_to = self.REWIND_BTN

    def onGotoButton(self):
        self.send_midi_to = self.GOTO_BTN

    def onRecordButton(self):
        self.send_midi_to = self.RECORD_BTN

    def onScenesButton(self):
        self.send_midi_to = self.SCENES_BTN

    def onSendInit(self):
        try:
            for note in self.parseInitCommand():
                self.gui.queue_out.put(note)
        except Exception as ex:
            QMessageBox.critical(self,
                                 "Invalid init commands",
                                 str(ex))

    def onCtrls(self):
        self.send_midi_to = self.CTRLS

    def onBlockBts(self):
        self.send_midi_to = self.BLOCK_BUTTONS

    def onStopClicked(self):
        self.send_midi_to = None

    def onBlack(self):
        self.lightAllCell(self.black_vel.value())

    def onGreen(self):
        self.lightAllCell(self.green_vel.value())

    def onBlinkGreen(self):
        self.lightAllCell(self.blink_green_vel.value())

    def onRed(self):
        self.lightAllCell(self.red_vel.value())

    def onBlinkRed(self):
        self.lightAllCell(self.blink_red_vel.value())

    def onAmber(self):
        self.lightAllCell(self.amber_vel.value())

    def onBlinkAmber(self):
        self.lightAllCell(self.blink_amber_vel.value())

    def lightAllCell(self, color):
        for line in self.device.start_stop:
            for data in line:
                (m, channel, pitch, v) = data
                note = ((self.NOTEON << 4) + channel, pitch, color)
                self.gui.queue_out.put(note)
        for btn_key in self.device.block_buttons:
            (msg_type, channel, pitch, velocity) = btn_key
            note = ((self.NOTEON << 4) + channel, pitch, color)
            self.gui.queue_out.put(note)

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

        channel = status & 0xF
        msg_type = status >> 4
        # -1: special value for velocity sensitive pad
        btn_id = (msg_type,
                  channel,
                  pitch,
                  -1 if velocity not in [0, 127] else velocity)
        btn_key = (msg_type >> 1, channel, pitch)
        ctrl_key = (msg_type, channel, pitch)

        if ctrl_key not in self.knownCtrl:
            # process controller
            if self.send_midi_to == self.MASTER_VOLUME_CTRL:
                if msg_type == self.MIDICTRL:
                    self.device.master_volume_ctrl = ctrl_key
                    (self.label_master_volume_ctrl
                     .setText(self.displayCtrl(ctrl_key)))
                    self.knownCtrl.add(ctrl_key)
                    self.send_midi_to = None

            elif self.send_midi_to == self.PLAY_BTN:
                self.send_midi_to = None
                self.knownCtrl.add(ctrl_key)
                self.knownBtn.add(btn_key)
                self.device.play_btn = btn_id
                self.playLabel.setText(self.displayCtrl(ctrl_key))
            elif self.send_midi_to == self.PAUSE_BTN:
                self.send_midi_to = None
                self.knownCtrl.add(ctrl_key)
                self.knownBtn.add(btn_key)
                self.device.pause_btn = btn_id
                self.pauseLabel.setText(self.displayCtrl(ctrl_key))
            elif self.send_midi_to == self.REWIND_BTN:
                self.send_midi_to = None
                self.knownCtrl.add(ctrl_key)
                self.knownBtn.add(btn_key)
                self.device.rewind_btn = btn_id
                self.rewindLabel.setText(self.displayCtrl(ctrl_key))
            elif self.send_midi_to == self.GOTO_BTN:
                self.send_midi_to = None
                self.knownCtrl.add(ctrl_key)
                self.knownBtn.add(btn_key)
                self.device.goto_btn = btn_id
                self.gotoLabel.setText(self.displayCtrl(ctrl_key))
            elif self.send_midi_to == self.RECORD_BTN:
                self.send_midi_to = None
                self.knownCtrl.add(ctrl_key)
                self.knownBtn.add(btn_key)
                self.device.record_btn = btn_id
                self.recordLabel.setText(self.displayCtrl(ctrl_key))

            elif self.send_midi_to == self.CTRLS:
                if msg_type == self.MIDICTRL:
                    cell = LearnCell(self)
                    cell.label.setText("Ch %s\n%s"
                                       % (channel + 1, pitch))
                    cell.setStyleSheet(self.NEW_CELL_STYLE_ROUND)
                    self.ctrlsHorizontalLayout.addWidget(cell)
                    self.device.ctrls.append(ctrl_key)
                    self.knownCtrl.add(ctrl_key)

            # then process other
            elif btn_key not in self.knownBtn:
                if self.send_midi_to == self.SCENES_BTN:
                    cell = LearnCell(self)
                    cell.label.setText("Ch %s\n%s"
                                       % (channel + 1,
                                          self.displayNote(pitch)))
                    cell.setStyleSheet(self.NEW_CELL_STYLE)
                    self.scenesHorizontalLayout.addWidget(cell)
                    self.device.scene_buttons.append(btn_id)
                    self.knownCtrl.add(ctrl_key)
                    self.knownBtn.add(btn_key)

                if self.send_midi_to == self.BLOCK_BUTTONS:
                    cell = LearnCell(self)
                    cell.label.setText("Ch %s\n%s"
                                       % (channel + 1,
                                          self.displayNote(pitch)))
                    cell.setStyleSheet(self.NEW_CELL_STYLE)
                    self.btsHorizontalLayout.addWidget(cell)
                    self.device.block_buttons.append(btn_id)
                    self.knownCtrl.add(ctrl_key)
                    self.knownBtn.add(btn_key)

                elif self.send_midi_to == self.START_STOP:
                    self.current_line_pitch.append(btn_id)
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
                    self.knownCtrl.add(ctrl_key)
                    self.knownBtn.add(btn_key)

    def accept(self):
        try:
            self.parseInitCommand()
            super(LearnDialog, self).accept()
        except Exception as ex:
            QMessageBox.critical(self,
                                 "Invalid init commands",
                                 str(ex))

    def reject(self):
        self.gui.is_learn_device_mode = False
        self.gui.redraw()
        super(LearnDialog, self).reject()

    def onSave(self):
        self.device.name = str(self.name.text())
        self.device.black_vel = int(self.black_vel.value())
        self.device.green_vel = int(self.green_vel.value())
        self.device.blink_green_vel = int(self.blink_green_vel.value())
        self.device.red_vel = int(self.red_vel.value())
        self.device.blink_red_vel = int(self.blink_red_vel.value())
        self.device.amber_vel = int(self.amber_vel.value())
        self.device.blink_amber_vel = int(self.blink_amber_vel.value())
        self.device.mapping['init_command'] = self.parseInitCommand()
        self.original_device.updateMapping(self.device.mapping)
        self.gui.is_learn_device_mode = False
        self.callback(self.original_device)
        self.gui.redraw()

    def displayNote(self, note_dec):
        octave, note = divmod(note_dec, 12)
        octave += 1
        note_str = self.NOTE_NAME[note]
        return note_str[:1] + str(octave) + note_str[1:]

    def displayCtrl(self, ctrl_key):
        (msg_type, channel, pitch) = ctrl_key
        if msg_type == self.NOTEON:
            type = "Note On"
            note = self.displayNote(pitch)
        elif msg_type == self.NOTEOFF:
            type = "Note Off"
            note = self.displayNote(pitch)
        elif msg_type == self.MIDICTRL:
            type = "Controller"
            note = str(pitch)
        else:
            type = "Type=%s" % msg_type
        return "Channel %s %s %s" % (channel + 1,
                                     type,
                                     note)

    def displayBtn(self, btn_id):
        (msg_type, channel, pitch, velocity) = btn_id
        ctrl_key = (msg_type, channel, pitch)
        return self.displayCtrl(ctrl_key)

    def parseInitCommand(self):
        raw_str = str(self.init_command.toPlainText())
        init_commands = []
        line = 1
        for raw_line in raw_str.split("\n"):
            matches = _init_cmd_regexp.match(raw_line)
            if matches:
                byte1 = int(matches.group(1))
                byte2 = int(matches.group(2))
                byte3 = int(matches.group(3))
                if not 0 <= byte1 < 256:
                    raise Exception("First number out of range on line %s"
                                    % line)
                if not 0 <= byte2 < 256:
                    raise Exception("Second number out of range on line %s"
                                    % line)
                if not 0 <= byte3 < 256:
                    raise Exception("Third number out of range on line %s"
                                    % line)
                init_commands.append((byte1, byte2, byte3))
            elif len(raw_line):
                raise Exception("Invalid format for Line %s :\n%s"
                                % (line, raw_line))
            line = line + 1
        return init_commands
