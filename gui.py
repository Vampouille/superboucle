#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Gui
"""

from PyQt5.QtWidgets import (QWidget,
                             QMainWindow,
                             QFileDialog)
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QSettings
from clip import Clip, load_song_from_file
from ui import Ui_MainWindow
from cell_ui import Ui_Cell
from learn import LearnDialog
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

    def addDevice(self, mapping):
        self.device = Device(mapping)
        self.device.save()
