from PyQt5.QtWidgets import QDialog, QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer
from queue import Queue, Empty
from learn_cell_ui import Ui_LearnCell
from learn_ui import Ui_Dialog
from device import Device
from midi_actions import MidiAction, MidiRowAction, MidiGridAction
import re

_init_cmd_regexp = re.compile("^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$")


class LearnCell(QWidget, Ui_LearnCell):
    def __init__(self, parent):
        super(LearnCell, self).__init__(parent)
        self.setupUi(self)


class LearnDialog(QDialog, Ui_Dialog):
    NEW_CELL_STYLE = ("#cell_frame {border: 0px; "
                      "border-radius: 5px; "
                      "background-color: rgb(217, 217, 217);}")
    NEW_CELL_STYLE_ROUND = ("#cell_frame {border: 0px; "
                            "border-radius: 20px; "
                            "background-color: rgb(217, 217, 217);}")
    STYLE_BLINK_ON = ("* {background-color: rgb(255, 127, 0);"
                      "border-radius: 5px;}")
    STYLE_BLINK_OFF = ("* {background-color: rgb(220, 220, 220);"
                       "border: 1px solid gray;"
                       "border-radius: 5px;}")

    MIDI_ACTION_CELL_STYLES = {
        'ctrls': NEW_CELL_STYLE_ROUND
    }

    NOTE_NAME = ['C', 'C#',
                 'D', 'D#',
                 'E',
                 'F', 'F#',
                 'G', 'G#',
                 'A', 'A#',
                 'B']

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

        # keep original values if cancel is clicked
        self.device = Device()
        self.device.update(self.original_device)

        self.updateUi.connect(self.update)

        # super shitty way to achieve blinking
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_blinking)
        self.timer.start(250)
        self.last_blinked = None

        # set current device values
        self.name.setText(self.device.name)
        self.name.textEdited.connect(self.onNameEdited)
        for k in self.device.output_mapping:
            try:
                input = getattr(self, k)
                handler = self.velocity_sender(input)
                input.valueChanged.connect(handler)
                test_button = getattr(self, 'test_' + k)
                test_button.clicked.connect(handler)
            except AttributeError as e:
                print('output attribute ' + k)
                print(str(e))
                pass

        self.sendInitButton.clicked.connect(self.onSendInit)

        for k in MidiAction.ALL_INSTANCES:
            try:
                listen_button = getattr(self, k + '_learn')
                listener = MidiAction.listener(k, self.device)
                listen_button.clicked.connect(listener)
                clear_button = getattr(self, k + '_clear')
                clearer = MidiAction.clearer(k, self.device,
                                             callback=self.update_gui)
                clear_button.clicked.connect(clearer)
            except AttributeError as e:
                print('input attribute ' + k)
                print(str(e))

        # connect signals
        self.accepted.connect(self.onSave)
        self.finished.connect(self.onFinish)

        self.stop1.clicked.connect(self.onStopClicked)
        self.stop2.clicked.connect(self.onStopClicked)
        self.stop3.clicked.connect(self.onStopClicked)

        self.update_gui()
        self.show()

    def onNameEdited(self, name):
        self.device.name = name

    def onStopClicked(self):
        MidiAction.LISTENING = None

    def onSendInit(self):
        try:
            raw_str = str(self.init_command.toPlainText())
            for note in self.parse_init_command(raw_str):
                self.gui.queue_out.put(note)
        except Exception as ex:
            QMessageBox.critical(self,
                                 "Invalid init commands",
                                 str(ex))

    def velocity_sender(self, input):
        def handler():
            v = input.value()
            self.device.output_mapping[input.objectName()] = v
            self.light_all_cell(v)

        return handler

    def light_all_cell(self, color):
        notes = self.device.generate_feedback_notes('start_stop', color)
        for note in notes:
            self.gui.queue_out.put(note)
            # block_buttons:

    def update(self):
        try:
            while True:
                data = self.queue.get(block=False)
                midi_message = Device.decode_midi(data)
                if MidiAction.LISTENING:
                    self.device.learn(midi_message)
                    self.update_gui()
        except Empty:
            pass

    def update_blinking(self):
        if self.last_blinked:
            self.last_blinked.setStyleSheet(self.STYLE_BLINK_OFF)
            self.last_blinked = None
        elif MidiAction.LISTENING:
            listen_button = getattr(self, MidiAction.LISTENING + '_learn')
            listen_button.setStyleSheet(self.STYLE_BLINK_ON)
            self.last_blinked = listen_button
            # MidiAction.LISTENING

    def update_gui(self):
        self.name.setText(self.device.name)
        for k, v in self.device.output_mapping.items():
            if k in ['init_command']:
                continue
            try:
                input = getattr(self, k)
                input.setValue(v)
            except AttributeError as e:
                print('output attribute ' + k)
                print(str(e))
                pass
        init_command_string = self.show_init_command(self.device.init_command)
        self.init_command.setText(init_command_string)

        for k in MidiAction.ALL_INSTANCES:
            try:
                midi_action = MidiAction.get(k, self.device)
                midi_data = midi_action.data
                if isinstance(midi_action, MidiGridAction):
                    self.updateGridAction(k, midi_data)
                elif isinstance(midi_action, MidiRowAction):
                    self.updateRowAction(k, midi_data)
                elif midi_data:
                    label = getattr(self, k + '_label')
                    text = self.displayMidi(midi_data)
                    label.setText(text)
                    # else:
                    #    print('not displaying bindingy for: ' + k)
            except AttributeError as e:
                print('input attribute ' + k)
                print(str(e))

    def updateRowAction(self, midi_action_name, midi_keys):
        layout = getattr(self, midi_action_name + '_layout')
        cell_style = self.MIDI_ACTION_CELL_STYLES.get(midi_action_name,
                                                      self.NEW_CELL_STYLE)
        # clear the layout
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        for midi_key in midi_keys:
            cell = LearnCell(self)
            text = self.displayMidi(midi_key, "Ch {chan}\n{note}")
            cell.label.setText(text)
            cell.setStyleSheet(cell_style)
            layout.addWidget(cell)

    def updateGridAction(self, midi_action_name, midi_key_table):
        learn_btn = getattr(self, midi_action_name + '_learn')
        learn_str = "Add Next" if len(midi_key_table) else "Learn First"
        learn_btn.setText(learn_str + " line")
        layout = getattr(self, midi_action_name + '_layout')
        cell_style = self.MIDI_ACTION_CELL_STYLES.get(midi_action_name,
                                                      self.NEW_CELL_STYLE)
        # clear the layout
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        for y, row in enumerate(midi_key_table):
            for x, midi_key in enumerate(row):
                cell = LearnCell(self)
                text = self.displayMidi(midi_key, "Ch {chan}\n{note}")
                cell.label.setText(text)
                cell.setStyleSheet(cell_style)
                layout.addWidget(cell, y, x)

    def accept(self):
        try:
            raw_str = str(self.init_command.toPlainText())
            self.parse_init_command(raw_str)
            super(LearnDialog, self).accept()
        except Exception as ex:
            QMessageBox.critical(self,
                                 "Invalid init commands",
                                 str(ex))

    def reject(self):
        self.gui.is_learn_device_mode = False
        self.gui.redraw()
        super(LearnDialog, self).reject()

    def onFinish(self, event):
        self.onStopClicked()
        self.timer.stop()

    def onSave(self):
        raw_str = str(self.init_command.toPlainText())
        self.device.init_command = self.parse_init_command(raw_str)

        self.original_device.update(self.device)
        self.gui.is_learn_device_mode = False
        self.callback(self.original_device)
        self.gui.redraw()

    def displayNote(self, note_dec):
        octave, note = divmod(note_dec, 12)
        octave += 1
        note_str = self.NOTE_NAME[note]
        return note_str[:1] + str(octave) + note_str[1:]

    def displayMidi(self, ctrl_key, pattern="Channel {chan} {type} {note}"):
        msg_type, channel, pitch = ctrl_key
        type_switch = {
            MidiAction.NOTEON: self.displayNote,
            MidiAction.NOTEOFF: self.displayNote
        }
        type_string = {
            MidiAction.NOTEON: "Note On",
            MidiAction.NOTEOFF: "Note Off",
            MidiAction.MIDICTRL: "Controller"
        }
        note = type_switch.get(msg_type, lambda x: x)(pitch)
        type = type_string.get(msg_type, "Type={}".format(msg_type))
        return pattern.format(chan=channel + 1, type=type, note=note)

    @staticmethod
    def parse_init_command(raw_str):
        init_commands = []
        for line, raw_line in enumerate(raw_str.split("\n")):
            matches = _init_cmd_regexp.match(raw_line)
            if matches:
                command = tuple(map(int, matches.groups()))
                for i, byte in enumerate(command):
                    if not byte in range(256):
                        raise Exception("{}. number out of range "
                                        "on line {}".format(i, line))
                init_commands.append(command)
            elif len(raw_line):
                raise Exception("Invalid format for Line %s :\n%s"
                                % (line, raw_line))
        return init_commands

    @staticmethod
    def show_init_command(init_command):
        return "\n".join([", ".join([str(num)
                                     for num in init_cmd])
                          for init_cmd in init_command])
