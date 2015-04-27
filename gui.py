#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Gui
"""

from PyQt5.QtWidgets import (QDialog,
                             QDial,
                             QWidget,
                             QApplication,
                             QMainWindow,
                             QFileDialog)
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QSettings, QPoint
from clip import Clip, load_song_from_file
from ui import Ui_MainWindow
from cell_ui import Ui_Cell
from learn_cell import Ui_LearnCell
import learn_ui
import struct
from queue import Queue, Empty
import json


class Device():

    NOTEON = 0x90
    NOTEOFF = 0x80

    pad_coord_to_note = [[36, 38, 40, 41],
                         [48, 50, 52, 53],
                         [60, 62, 64, 65],
                         [72, 74, 76, 77]]

    def __init__(self, mapping):
        self.note_to_coord = {}
        self.mapping = mapping
        for x in range(len(mapping['start_stop'])):
            line = mapping['start_stop'][x]
            for y in range(len(line)):
                self.note_to_coord[line[y]] = (x, y)
        self.state_to_color = {Clip.STOP: 12,
                               Clip.STARTING: 13,
                               Clip.START: 14,
                               Clip.STOPPING: 15}

    def getXY(self, note):
        return self.note_to_coord[note]

    # TODO implements note, second note and channel
    def generateNote(self, x, y, state):
        print("Generate note for cell {0} {1} and state {2}".
              format(x, y, state))
        note = self.mapping['start_stop'][x][y]
        velocity = self.state_to_color[state]
        return (self.NOTEON, note, velocity)

    def __str__(self):
        return str(self.mapping)

    def save(self):
        settings = QSettings('superboucle', 'superboucle')
        if settings.contains('devices'):
            devices = settings.value('devices')
        else:
            devices = []
        devices.append(json.dumps(self.mapping))
        settings.setValue('devices', devices)

    @property
    def name(self):
        return self.mapping['name']


class LearnCell(QWidget, Ui_LearnCell):

    def __init__(self, parent):
        super(LearnCell, self).__init__(parent)
        self.setupUi(self)


class LearnDialog(QDialog, learn_ui.Ui_Dialog):

    NOTEON = 0x9
    NOTEOFF = 0x8
    NEW_CELL_STYLE = "border: 0px; border-radius: 10px; background-color: rgb(217, 217, 217);"

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
        self.gui.addDevice(Device(self.mapping))


class Cell(QWidget, Ui_Cell):

    def __init__(self, parent, clip, x, y):
        super(Cell, self).__init__(parent)

        self.pos_x, self.pos_y = x, y
        self.clip = clip
        self.blink, self.color = False, None
        self.setupUi(self)
        self.setStyleSheet(Gui.DEFAULT)
        if clip:
            self.clip_name.setText(clip.name)
            self.start_stop.clicked.connect(parent.onStartStopClick)
            self.edit.clicked.connect(parent.onEdit)
        else:
            self.start_stop.setEnabled(False)
            self.clip_position.setEnabled(False)
            self.edit.setText("Add Clip...")
            self.edit.clicked.connect(parent.onAddClipClick)


class Gui(QMainWindow, Ui_MainWindow):

    NOTEON = 0x9
    NOTEOFF = 0x8

    GREEN = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(125,242,0);}"
    BLUE = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(0, 130, 240);}"
    RED = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(255, 21, 65);}"
    PURPLE = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(130, 0, 240);}"
    DEFAULT = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(217, 217, 217);}"

    STATE_COLORS = {Clip.STOP: RED,
                    Clip.STARTING: GREEN,
                    Clip.START: GREEN,
                    Clip.STOPPING: RED}
    STATE_BLINK = {Clip.STOP: False,
                   Clip.STARTING: True,
                   Clip.START: False,
                   Clip.STOPPING: True}

    BLINK_DURATION = 200
    PROGRESS_PERIOD = 100

    updateUi = pyqtSignal()
    readQueueIn = pyqtSignal()

    def __init__(self, song):
        QObject.__init__(self)
        super(Gui, self).__init__()
        self.setupUi(self)
        self.clip_volume.knobRadius = 3
        self.is_add_device_mode = False
        self.queue_out, self.queue_in = Queue(), Queue()
        self.updateUi.connect(self.update)
        self.readQueueIn.connect(self.readQueue)

        self.actionOpen.triggered.connect(self.onActionOpen)
        self.actionSave.triggered.connect(self.onActionSave)
        self.actionSave_As.triggered.connect(self.onActionSaveAs)
        self.actionAdd_Device.triggered.connect(self.onAddDevice)
        self.master_volume.valueChanged.connect(self.onMasterVolumeChange)
        self.clip_name.textChanged.connect(self.onClipNameChange)
        self.clip_volume.valueChanged.connect(self.onClipVolumeChange)
        self.beat_diviser.valueChanged.connect(self.onBeatDiviserChange)
        self.frame_offset.valueChanged.connect(self.onFrameOffsetChange)
        self.beat_offset.valueChanged.connect(self.onBeatOffsetChange)

        self.blktimer = QTimer()
        self.blktimer.state = False
        self.blktimer.timeout.connect(self.toogleBlinkButton)

        self.disptimer = QTimer()
        self.disptimer.start(self.PROGRESS_PERIOD)
        self.disptimer.timeout.connect(self.updateProgress)

        settings = QSettings('superboucle', 'superboucle')
        if settings.contains('devices'):
            devices = settings.value('devices')
            if len(devices):
                self.device = Device(json.loads(devices[0]))
                print("Setting first configured device %s" % self.device)
        else:
            self.device = Device({'start_stop': Device.pad_coord_to_note})
            print("setting default device")

        # Avoid missing song attribute on master volume changed
        # self.song = song
        self.initUI(song)
        self.show()

    def initUI(self, song):

        # remove old buttons
        self.btn_matrix = [[None for x in range(song.height)]
                           for x in range(song.width)]
        self.state_matrix = [[-1 for x in range(song.height)]
                             for x in range(song.width)]
        for i in reversed(range(self.gridLayout.count())):
            self.gridLayout.itemAt(i).widget().close()
            self.gridLayout.itemAt(i).widget().setParent(None)

        self.song = song
        self.frame_clip.setEnabled(False)
        self.master_volume.setValue(song.volume*256)
        for x in range(song.width):
            for y in range(song.height):
                clip = song.clips_matrix[x][y]
                cell = Cell(self, clip, x, y)
                self.btn_matrix[x][y] = cell
                self.gridLayout.addWidget(cell, x, y)

        self.update()

    def onStartStopClick(self):
        clip = self.sender().parent().parent().clip
        self.song.toogle(clip.x, clip.y)
        self.update()

    def onEdit(self):
        self.last_clip = self.sender().parent().parent().clip
        if self.last_clip:
            self.frame_clip.setEnabled(True)
            self.clip_name.setText(self.last_clip.name)
            self.frame_offset.setValue(self.last_clip.frame_offset)
            self.beat_offset.setValue(self.last_clip.beat_offset)
            self.beat_diviser.setValue(self.last_clip.beat_diviser)
            self.clip_volume.setValue(self.last_clip.volume*256)
            self.clip_description.setText("Good clip !")

    def onAddClipClick(self):
        sender = self.sender().parent().parent()
        audio_file, a = QFileDialog.getOpenFileName(self,
                                                    'Open Clip file',
                                                    ('/home/joe/git'
                                                     '/superboucle/'),
                                                    'All files (*.*)')
        if audio_file:
            new_clip = Clip(audio_file)
            sender.clip = new_clip
            sender.clip_name.setText(new_clip.name)
            sender.start_stop.clicked.connect(self.onStartStopClick)
            print(sender.edit.text())
            sender.edit.setText("Edit")
            sender.edit.clicked.disconnect(self.onAddClipClick)
            sender.edit.clicked.connect(self.onEdit)
            sender.start_stop.setEnabled(True)
            sender.clip_position.setEnabled(True)
            self.song.add_clip(new_clip, sender.pos_x, sender.pos_y)
            self.update()

    def onMasterVolumeChange(self):
        self.song.volume = (self.master_volume.value() / 256)

    def onClipNameChange(self):
        self.last_clip.name = self.clip_name.text()
        tframe = self.btn_matrix[self.last_clip.x][self.last_clip.y]
        tframe.clip_name.setText(self.last_clip.name)

    def onClipVolumeChange(self):
        self.last_clip.volume = (self.clip_volume.value() / 256)

    def onBeatDiviserChange(self):
        self.last_clip.beat_diviser = self.beat_diviser.value()

    def onFrameOffsetChange(self):
        self.last_clip.frame_offset = self.frame_offset.value()

    def onBeatOffsetChange(self):
        self.last_clip.beat_offset = self.beat_offset.value()

    def onActionOpen(self):
        file_name, a = (
            QFileDialog.getOpenFileName(self,
                                        'Open file',
                                        '/home/joe/git/superboucle/',
                                        'Super Boucle Song (*.sbl)'))
        if file_name:
            self.setEnabled(False)
            self.initUI(load_song_from_file(file_name))
            self.setEnabled(True)

    def onActionSave(self):
        if self.song.file_name:
            self.song.save()
            print("File saved")
        else:
            self.onActionSaveAs()

    def onActionSaveAs(self):
        self.song.file_name, a = (
            QFileDialog.getSaveFileName(self,
                                        'Save As',
                                        '/home/joe/git/superboucle/',
                                        'Super Boucle Song (*.sbl)'))
        if self.song.file_name:
            self.song.save()
            print("File saved to : {}".format(self.song.file_name))

    def onAddDevice(self):
        self.add_device = LearnDialog(self)
        self.is_add_device_mode = True

    def update(self):
        for clp in self.song.clips:
            # print("updating clip at {0} {1}".format(clp.x, clp.y))
            if clp.state != self.state_matrix[clp.x][clp.y]:
                self.setCellColor(clp.x,
                                  clp.y,
                                  self.STATE_COLORS[clp.state],
                                  self.STATE_BLINK[clp.state])
                self.queue_out.put(self.device.generateNote(clp.x,
                                                            clp.y,
                                                            clp.state))
                self.state_matrix[clp.x][clp.y] = clp.state

    def readQueue(self):
        updateUi = False
        try:
            while True:
                note = self.queue_in.get(block=False)
                if len(note) == 3:
                    status, pitch, vel = struct.unpack('3B', note)
                    print("Note received {0} {1} {2}".
                          format(status, pitch, vel))
                    try:
                        x, y = self.device.getXY(pitch)
                        if status >> 4 == self.NOTEOFF and x >= 0 and y >= 0:
                            self.song.toogle(x, y)
                            updateUi = True
                    except KeyError:
                        pass
        except Empty:
            pass
        if updateUi:
            self.update()

    def setCellColor(self, x, y, color, blink=False):
        self.btn_matrix[x][y].setStyleSheet(color)
        self.btn_matrix[x][y].blink = blink
        self.btn_matrix[x][y].color = color
        if blink and not self.blktimer.isActive():
            self.blktimer.state = False
            self.blktimer.start(self.BLINK_DURATION)
        if not blink and self.blktimer.isActive():
            if not any([btn.blink for line in self.btn_matrix
                        for btn in line]):
                self.blktimer.stop()

    def toogleBlinkButton(self):
        for line in self.btn_matrix:
            for btn in line:
                if btn.blink:
                    if self.blktimer.state:
                        btn.setStyleSheet(btn.color)
                    else:
                        btn.setStyleSheet(self.DEFAULT)

        self.blktimer.state = not self.blktimer.state

    def updateProgress(self):
        for line in self.btn_matrix:
            for btn in line:
                if btn.clip:
                    btn.clip_position.setValue((
                        (btn.clip.last_offset / btn.clip.length) * 100))

    def addDevice(self, device):
        self.device = device
        device.save()
