#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Gui
"""

from PyQt5.QtWidgets import (QWidget, QMainWindow, QFileDialog,
                             QAction, QActionGroup, QMessageBox)
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QSettings
from clip import Clip, load_song_from_file
from gui_ui import Ui_MainWindow
from cell_ui import Ui_Cell
from learn import LearnDialog
from manage import ManageDialog
from new_song import NewSongDialog
from add_clip import AddClipDialog
from device import Device
import struct
from queue import Queue, Empty
import pickle
from os.path import expanduser

BAR_START_TICK = 0.0
BEATS_PER_BAR = 4.0
BEAT_TYPE = 4.0
TICKS_PER_BEAT = 960.0


def frame2bbt(frame, ticks_per_beat, beats_per_minute, frame_rate):
    ticks_per_second = (beats_per_minute * ticks_per_beat) / 60
    return (ticks_per_second * frame) / frame_rate


def pos2str(pos):
    return """Position :
        Unique 1 : %s
        Usecs : %s
        frame rate : %s
        frame : %s
        valid : %s
        bar : %s
        beat : %s
        tick : %s
        bar_start_tick : %s
        beats_per_bar : %s
        beat_type : %s
        ticks_per_beat : %s
        beats_per_minute : %s
        frame_time : %s
        next_time : %s
        bbt_offset : %s
        audio_frames_per_video_frame : %s
        video_offset : %s
        unique_2 : %s
    """ % (pos.unique_1,
           pos.usecs,
           pos.frame_rate,
           pos.frame,
           pos.valid,
           pos.bar,
           pos.beat,
           pos.tick,
           pos.bar_start_tick,
           pos.beats_per_bar,
           pos.beat_type,
           pos.ticks_per_beat,
           pos.beats_per_minute,
           pos.frame_time,
           pos.next_time,
           pos.bbt_offset,
           pos.audio_frames_per_video_frame,
           pos.video_offset,
           pos.unique_2)


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
            self.start_stop.clicked.connect(parent.onStartStopClicked)
            self.edit.clicked.connect(parent.onEdit)
        else:
            self.start_stop.setEnabled(False)
            self.clip_position.setEnabled(False)
            self.edit.setText("Add Clip...")
            self.edit.clicked.connect(parent.onAddClipClicked)


class Gui(QMainWindow, Ui_MainWindow):

    NOTEON = 0x9
    NOTEOFF = 0x8
    MIDICTRL = 11

    GREEN = ("#cell_frame { border: 0px; border-radius: 10px; "
             "background-color: rgb(125,242,0);}")
    BLUE = ("#cell_frame { border: 0px; border-radius: 10px; "
            "background-color: rgb(0, 130, 240);}")
    RED = ("#cell_frame { border: 0px; border-radius: 10px; "
           "background-color: rgb(255, 21, 65);}")
    PURPLE = ("#cell_frame { border: 0px; border-radius: 10px; "
              "background-color: rgb(130, 0, 240);}")
    DEFAULT = ("#cell_frame { border: 0px; border-radius: 10px; "
               "background-color: rgb(217, 217, 217);}")

    STATE_COLORS = {Clip.STOP: RED,
                    Clip.STARTING: GREEN,
                    Clip.START: GREEN,
                    Clip.STOPPING: RED}
    STATE_BLINK = {Clip.STOP: False,
                   Clip.STARTING: True,
                   Clip.START: False,
                   Clip.STOPPING: True}

    BLINK_DURATION = 200
    PROGRESS_PERIOD = 300

    updateUi = pyqtSignal()
    readQueueIn = pyqtSignal()

    def __init__(self, song, jack_client):
        QObject.__init__(self)
        super(Gui, self).__init__()
        self._jack_client = jack_client
        self.setupUi(self)
        self.clip_volume.knobRadius = 3
        self.is_learn_device_mode = False
        self.queue_out, self.queue_in = Queue(), Queue()
        self.updateUi.connect(self.update)
        self.readQueueIn.connect(self.readQueue)
        self.current_vol_block = 0

        # Load devices
        self.deviceGroup = QActionGroup(self.menuDevice)
        self.devices = []
        settings = QSettings('superboucle', 'devices')
        if settings.contains('devices') and settings.value('devices'):
            for raw_device in settings.value('devices'):
                self.devices.append(Device(pickle.loads(raw_device)))
        else:
            self.devices.append(Device({'name': 'No Device', }))
        self.updateDevices()
        self.deviceGroup.triggered.connect(self.onDeviceSelect)

        # Load song
        self.initUI(song)

        self.actionNew.triggered.connect(self.onActionNew)
        self.actionOpen.triggered.connect(self.onActionOpen)
        self.actionSave.triggered.connect(self.onActionSave)
        self.actionSave_As.triggered.connect(self.onActionSaveAs)
        self.actionAdd_Device.triggered.connect(self.onAddDevice)
        self.actionManage_Devices.triggered.connect(self.onManageDevice)
        self.actionFullScreen.triggered.connect(self.onActionFullScreen)
        self.master_volume.valueChanged.connect(self.onMasterVolumeChange)
        self.rewindButton.clicked.connect(self.onRewindClicked)
        self.playButton.clicked.connect(self._jack_client.transport_start)
        self.pauseButton.clicked.connect(self._jack_client.transport_stop)
        self.gotoButton.clicked.connect(self.onGotoClicked)
        self.clip_name.textChanged.connect(self.onClipNameChange)
        self.clip_volume.valueChanged.connect(self.onClipVolumeChange)
        self.beat_diviser.valueChanged.connect(self.onBeatDiviserChange)
        self.frame_offset.valueChanged.connect(self.onFrameOffsetChange)
        self.beat_offset.valueChanged.connect(self.onBeatOffsetChange)
        self.deleteButton.clicked.connect(self.onDeleteClipClicked)

        self.blktimer = QTimer()
        self.blktimer.state = False
        self.blktimer.timeout.connect(self.toogleBlinkButton)

        self.disptimer = QTimer()
        self.disptimer.start(self.PROGRESS_PERIOD)
        self.disptimer.timeout.connect(self.updateProgress)

        self._jack_client.set_timebase_callback(self.timebase_callback)

        self.show()

    def initUI(self, song):

        # remove old buttons
        self.btn_matrix = [[None for y in range(song.height)]
                           for x in range(song.width)]
        self.state_matrix = [[-1 for y in range(song.height)]
                             for x in range(song.width)]
        for i in reversed(range(self.gridLayout.count())):
            self.gridLayout.itemAt(i).widget().close()
            self.gridLayout.itemAt(i).widget().setParent(None)

        self.song = song
        self.frame_clip.setEnabled(False)
        self.master_volume.setValue(song.volume*256)
        self.bpm.setValue(song.bpm)
        self.beat_per_bar.setValue(song.beat_per_bar)
        for x in range(song.width):
            for y in range(song.height):
                clip = song.clips_matrix[x][y]
                cell = Cell(self, clip, x, y)
                self.btn_matrix[x][y] = cell
                self.gridLayout.addWidget(cell, y, x)

        # send init command
        for init_cmd in self.device.init_command:
            self.queue_out.put(init_cmd)

        self.update()

    def closeEvent(self, event):
        settings = QSettings('superboucle', 'devices')
        settings.setValue('devices',
                          [pickle.dumps(x.mapping) for x in self.devices])

    def onStartStopClicked(self):
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
            state, position = self._jack_client.transport_query()
            fps = position['frame_rate']
            bps = self.bpm.value() / 60
            if self.bpm.value() and fps:
                size_in_beat = (bps/fps)*self.song.length(self.last_clip)
            else:
                size_in_beat = "No BPM info"
            clip_description = ("Size in sample : %s\nSize in beat : %s"
                                % (self.song.length(self.last_clip),
                                   round(size_in_beat, 1)))

            self.clip_description.setText(clip_description)

    def onAddClipClicked(self):
        AddClipDialog(self, self.sender().parent().parent())

    def onDeleteClipClicked(self):
        if self.last_clip:
            response = QMessageBox.question(self,
                                            "Delete Clip ?",
                                            ("Are you sure "
                                             "to delete the clip ?"))
            if response == QMessageBox.Yes:
                self.frame_clip.setEnabled(False)
                self.song.removeClip(self.last_clip)
                self.initUI(self.song)

    def onMasterVolumeChange(self):
        self.song.volume = (self.master_volume.value() / 256)

    def onStartClicked(self):
        pass
        self._jack_client.transport_start

    def onGotoClicked(self):
        state, position = self._jack_client.transport_query()
        new_position = (position['beats_per_bar']
                        * (self.gotoTarget.value() - 1)
                        * position['frame_rate']
                        * (60 / position['beats_per_minute']))
        self._jack_client.transport_locate(int(round(new_position, 0)))

    def onRewindClicked(self):
        self._jack_client.transport_locate(0)

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

    def onActionNew(self):
        NewSongDialog(self)

    def onActionOpen(self):
        file_name, a = (
            QFileDialog.getOpenFileName(self,
                                        'Open file',
                                        expanduser('~'),
                                        'Super Boucle Song (*.sbs)'))
        if file_name:
            self.setEnabled(False)
            message = QMessageBox(self)
            message.setWindowTitle("Loading ....")
            message.setText("Reading Files, please wait ...")
            message.show()
            self.initUI(load_song_from_file(file_name))
            message.close()
            self.setEnabled(True)

    def onActionSave(self):
        if self.song.file_name:
            self.song.save()
        else:
            self.onActionSaveAs()

    def onActionSaveAs(self):
        self.song.file_name, a = (
            QFileDialog.getSaveFileName(self,
                                        'Save As',
                                        expanduser('~'),
                                        'Super Boucle Song (*.sbs)'))
        if self.song.file_name:
            self.song.save()
            print("File saved to : {}".format(self.song.file_name))

    def onAddDevice(self):
        self.learn_device = LearnDialog(self, self.addDevice)
        self.is_learn_device_mode = True

    def onManageDevice(self):
        ManageDialog(self)

    def onActionFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self.show()

    def update(self):
        for x in range(len(self.song.clips_matrix)):
            line = self.song.clips_matrix[x]
            for y in range(len(line)):
                clp = line[y]
                if clp is None:
                    state = None
                else:
                    state = clp.state
                if state != self.state_matrix[x][y]:
                    if clp:
                        self.setCellColor(x,
                                          y,
                                          self.STATE_COLORS[state],
                                          self.STATE_BLINK[state])
                    try:
                        self.queue_out.put(self.device.generateNote(x,
                                                                    y,
                                                                    state))
                    except IndexError:
                        # print("No cell associated to %s x %s"
                        # % (clp.x, clp.y))
                        pass
                self.state_matrix[x][y] = state

    def redraw(self):
        self.state_matrix = [[-1 for x in range(self.song.height)]
                             for x in range(self.song.width)]
        self.update()

    def readQueue(self):
        try:
            while True:
                note = self.queue_in.get(block=False)
                if len(note) == 3:
                    status, pitch, vel = struct.unpack('3B', note)
                    channel = status & 0xF
                    msg_type = status >> 4
                    self.processNote(msg_type, channel, pitch, vel)
                else:
                    print("Invalid message length")
        except Empty:
            pass

    def processNote(self, msg_type, channel, pitch, vel):

        btn_key = (msg_type, channel, pitch, vel)
        ctrl_key = (msg_type, channel, pitch)

        # master volume
        if ctrl_key == self.device.master_volume_ctrl:
            self.song.master_volume = vel / 127
            (self.master_volume
             .setValue(self.song.master_volume * 256))
        elif btn_key == self.device.play_btn:
            self._jack_client.transport_start()
        elif btn_key == self.device.pause_btn:
            self._jack_client.transport_stop()
        elif btn_key == self.device.rewind_btn:
            self.onRewindClicked()
        elif btn_key == self.device.goto_btn:
            self.onGotoClicked()
        elif ctrl_key in self.device.ctrls:
            try:
                ctrl_index = self.device.ctrls.index(ctrl_key)
                clip = (self.song.clips_matrix
                        [ctrl_index]
                        [self.current_vol_block])
                if clip:
                    clip.volume = vel / 127
            except KeyError:
                pass
        elif btn_key in self.device.block_buttons:
            self.current_vol_block = self.device.block_buttons.index(btn_key)
            for i in range(len(self.device.block_buttons)):
                (a, b_channel, b_pitch, b) = self.device.block_buttons[i]
                if i == self.current_vol_block:
                    color = self.device.red_vel
                else:
                    color = self.device.black_vel
                self.queue_out.put(((self.NOTEON << 4) + b_channel,
                                    b_pitch,
                                    color))
        else:
            try:
                x, y = self.device.getXY(btn_key)
                if (x >= 0 and y >= 0):
                    self.song.toogle(x, y)
                    self.update()
            except IndexError:
                pass
            except KeyError:
                pass

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
        state, pos = self._jack_client.transport_query()
        if 'bar' in pos:
            bbt = "%d|%d|%03d" % (pos['bar'], pos['beat'], pos['tick'])
        else:
            bbt = "-|-|-"
        seconds = int(pos['frame'] / pos['frame_rate'])
        (minutes, second) = divmod(seconds, 60)
        (hour, minute) = divmod(minutes, 60)
        time = "%d:%02d:%02d" % (hour, minute, second)
        self.bbtLabel.setText("%s\n%s" % (bbt, time))
        for line in self.btn_matrix:
            for btn in line:
                if btn.clip and btn.clip.audio_file:
                    value = ((btn.clip.last_offset
                              / self.song.length(btn.clip))
                             * 97)
                    btn.clip_position.setValue(value)
                    btn.clip_position.repaint()

    def updateDevices(self):
        for action in self.deviceGroup.actions():
            self.deviceGroup.removeAction(action)
            self.menuDevice.removeAction(action)
        for device in self.devices:
            action = QAction(device.name, self.menuDevice)
            action.setCheckable(True)
            action.setData(device)
            self.menuDevice.addAction(action)
            self.deviceGroup.addAction(action)
        action.setChecked(True)
        self.device = device

    def addDevice(self, device):
        self.devices.append(device)
        self.updateDevices()
        self.is_learn_device_mode = False

    def onDeviceSelect(self):
        self.device = self.deviceGroup.checkedAction().data()
        if self.device:
            if self.device.init_command:
                for note in self.device.init_command:
                    self.queue_out.put(note)
            self.redraw()

    def timebase_callback(self, state, nframes, pos, new_pos):
        pos.valid = 0x10
        pos.bar_start_tick = BAR_START_TICK
        pos.beats_per_bar = self.beat_per_bar.value()
        pos.beat_type = BEAT_TYPE
        pos.ticks_per_beat = TICKS_PER_BEAT
        pos.beats_per_minute = self.bpm.value()
        ticks = frame2bbt(pos.frame,
                          pos.ticks_per_beat,
                          pos.beats_per_minute,
                          pos.frame_rate)
        (beats, pos.tick) = divmod(int(round(ticks, 0)),
                                   int(round(pos.ticks_per_beat, 0)))
        (bar, beat) = divmod(beats, int(round(pos.beats_per_bar, 0)))
        (pos.bar, pos.beat) = (bar + 1, beat + 1)
        return None
