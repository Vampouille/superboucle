#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Gui
"""

from PyQt5.QtWidgets import (QDialog,
                             QFrame,
                             QWidget,
                             QApplication,
                             QMainWindow,
                             QFileDialog)
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
import clip
from ui import Ui_MainWindow
from cell_ui import Ui_Cell
from learn_cell import Ui_LearnCell
import learn_ui
import struct
from queue import Queue, Empty


class Communicate(QtCore.QObject):

    updateUI = QtCore.pyqtSignal()


class LearnCell(QWidget, Ui_LearnCell):

    def __init__(self, parent):
        super(LearnCell, self).__init__(parent)
        self.setupUi(self)


class LearnDialog(QDialog, learn_ui.Ui_Dialog):

    NOTEON = 0x9
    NOTEOFF = 0x8
    NEW_CELL_STYLE = "border: 0px; border-radius: 10px; background-color: rgb(217, 217, 217);"

    def __init__(self, parent):
        super(LearnDialog, self).__init__(parent)
        self.gui = parent
        self.queue = Queue()
        self.current_line = None
        self.current_row = None
        self.pitch_matrix = []
        self.setupUi(self)
        self.show()
        self.accepted.connect(self.onSave)
        self.firstLine.clicked.connect(self.onFirstLineClicked)

    def onFirstLineClicked(self):

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

    def onNote(self, note):
        self.queue.put(note)

    def processNotes(self):
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
        if self.current_line is not None and self.current_line is not None:
            if status >> 4 == self.NOTEOFF:
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

    def onSave(self):
        self.pitch_matrix.append(self.current_line_pitch)
        pass

        print(self.pitch_matrix)
        self.gui.is_add_device_mode = False



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

    GREEN = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(125,242,0);}"
    BLUE = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(0, 130, 240);}"
    RED = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(255, 21, 65);}"
    PURPLE = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(130, 0, 240);}"
    DEFAULT = "#cell_frame { border: 0px; border-radius: 10px; background-color: rgb(217, 217, 217);}"

    STATE_COLORS = {clip.Clip.STOP: RED,
                    clip.Clip.STARTING: GREEN,
                    clip.Clip.START: GREEN,
                    clip.Clip.STOPPING: RED}
    STATE_BLINK = {clip.Clip.STOP: False,
                   clip.Clip.STARTING: True,
                   clip.Clip.START: False,
                   clip.Clip.STOPPING: True}

    BLINK_DURATION = 200
    PROGRESS_PERIOD = 100

    def __init__(self, song):
        super(Gui, self).__init__()
        self.setupUi(self)
        self.clip_volume.knobRadius = 3
        self.is_add_device_mode = False
        self.show()

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

        # Avoid missing song attribute on master volume changed
        self.song = song
        self.initUI(song)
        self.c = Communicate()

    def initUI(self, song):

        self.frame_clip.setEnabled(False)

        self.master_volume.setValue(song.volume*256)

        self.btn_matrix = [[None for x in range(song.height)]
                           for x in range(song.width)]
        self.state_matrix = [[-1 for x in range(song.height)]
                             for x in range(song.width)]

        for i in reversed(range(self.gridLayout.count())):
            self.gridLayout.itemAt(i).widget().close()
            self.gridLayout.itemAt(i).widget().setParent(None)

        for x in range(song.width):
            for y in range(song.height):
                clip = song.clips_matrix[x][y]
                cell = Cell(self, clip, x, y)
                self.btn_matrix[x][y] = cell
                self.gridLayout.addWidget(cell, x, y)

        song.registerUI(self.update)
        self.song = song
        self.update()

    def onStartStopClick(self):
        clip = self.sender().parent().parent().clip
        self.song.toogle(clip.x, clip.y)

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
            new_clip = clip.Clip(audio_file)
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
            self.initUI(clip.load_song_from_file(file_name))
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
        self.is_add_device_mode = True
        self.add_device = LearnDialog(self)
        self.c.updateUI.connect(self.add_device.processNotes)

    def update(self):
        for clp in self.song.clips:
            # print("updating clip at {0} {1}".format(clp.x, clp.y))
            if clp.state != self.state_matrix[clp.x][clp.y]:
                self.setCellColor(clp.x,
                                  clp.y,
                                  self.STATE_COLORS[clp.state],
                                  self.STATE_BLINK[clp.state])
                self.state_matrix[clp.x][clp.y] = clp.state

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

    def updateAddDeviceUi(self):
        self.c.updateUI.emit()


class PadUI():

    NOTEON = 0x9
    NOTEOFF = 0x8

    pad_note_to_coord = {36: (0, 0), 38: (0, 1), 40: (0, 2), 41: (0, 3),
                         48: (1, 0), 50: (1, 1), 52: (1, 2), 53: (1, 3),
                         60: (2, 0), 62: (2, 1), 64: (2, 2), 65: (2, 3),
                         72: (3, 0), 74: (3, 1), 76: (3, 2), 77: (3, 3)}

    pad_coord_to_note = [[36, 38, 40, 41],
                         [48, 50, 52, 53],
                         [60, 62, 64, 65],
                         [72, 74, 76, 77]]

    pad_state_to_color = {clip.Clip.STOP: 12,
                          clip.Clip.STARTING: 13,
                          clip.Clip.START: 14,
                          clip.Clip.STOPPING: 15}

    def __init__(self, width, height):
        self.state_matrix = [[-1 for x in range(height)]
                             for x in range(width)]

    def updatePad(self, song):
        res = []
        song.updatePadUI = False
        for x in range(song.width):
            for y in range(song.height):
                clip = song.clips_matrix[x][y]
                if clip:
                    if clip.state != self.state_matrix[x][y]:
                        print("Will update pad cell {0} {1} to state {2}".
                              format(x, y, clip.state))
                        res.append(self.generateNote(x, y, clip.state))
                        self.state_matrix[x][y] = clip.state
        return res

    def processNote(self, song, notes):
        for note in notes:
            if len(note) == 3:
                status, pitch, vel = struct.unpack('3B', note)
                print("Note received {0} {1} {2}".
                      format(status, pitch, vel))
                try:
                    x, y = self.getXY(pitch)

                    if status >> 4 == self.NOTEOFF and x >= 0 and y >= 0:
                        song.toogle(x, y)
                except KeyError:
                    pass

    def getXY(self, note):
        return self.pad_note_to_coord[note]

    def generateNote(self, x, y, state):
        print("Generate note for cell {0} {1} and state {2}".
              format(x, y, state))
        note = self.pad_coord_to_note[x][y]
        velocity = self.pad_state_to_color[state]
        return (self.NOTEON, note, velocity)



def main():
    app = QApplication()
    clip = Clip('beep-stereo.wav', beat_diviser=4, frame_offset=0, beat_offset=1)  # 1500
    song = Song(8, 8)
    song.add_clip(clip, 1, 2)

    app = QApplication()
    Gui(song)
    app.exec_()
   


if __name__ == '__main__':
    main()
