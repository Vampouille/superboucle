#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Gui
"""
from PyQt5.QtWidgets import (QMainWindow, QFileDialog,
                             QAction, QActionGroup, QMessageBox, QApplication)
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QSettings, Qt
from superboucle.clip import Clip
from superboucle.edit_clip import EditClipDialog
from superboucle.gui_ui import Ui_MainWindow
from superboucle.cell import Cell
from superboucle.learn import LearnDialog
from superboucle.device_manager import ManageDialog
from superboucle.playlist import PlaylistDialog
from superboucle.scene_manager import SceneManager
from superboucle.port_manager import PortManager
from superboucle.new_song import NewSongDialog
from superboucle.add_clip import AddClipDialog
from superboucle.device import Device
from superboucle.edit_midi import EditMidiDialog
from superboucle.clip_midi import MidiClip, MidiNote

import struct
from queue import Queue, Empty
import pickle
from os.path import expanduser, dirname, isfile

from superboucle.song import Song, verify_ext

SYNC_SOURCE_JACK = 0
SYNC_SOURCE_MIDI = 1

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
    AMBER = ("#cell_frame { border: 0px; border-radius: 10px; "
             "background-color: rgb(255, 102, 0);}")
    PURPLE = ("#cell_frame { border: 0px; border-radius: 10px; "
              "background-color: rgb(130, 0, 240);}")
    DEFAULT = ("#cell_frame { border: 0px; border-radius: 10px; "
               "background-color: rgb(217, 217, 217);}")

    RECORD_BLINK = ("QPushButton {background-color: rgb(255, 255, 255);}"
                    "QPushButton:pressed {background-color: "
                    "rgb(98, 98, 98);}")

    RECORD_DEFAULT = ("QPushButton {background-color: rgb(0, 0, 0);}"
                      "QPushButton:pressed {background-color: "
                      "rgb(98, 98, 98);}")

    STATE_COLORS = {Clip.STOP: RED,
                    Clip.STARTING: GREEN,
                    Clip.START: GREEN,
                    Clip.STOPPING: RED,
                    Clip.PREPARE_RECORD: AMBER,
                    Clip.RECORDING: AMBER}
    STATE_BLINK = {Clip.STOP: False,
                   Clip.STARTING: True,
                   Clip.START: False,
                   Clip.STOPPING: True,
                   Clip.PREPARE_RECORD: True,
                   Clip.RECORDING: False}

    BLINK_DURATION = 200
    PROGRESS_PERIOD = 300


    updateUi = pyqtSignal()
    readQueueIn = pyqtSignal()
    updatePorts = pyqtSignal()
    songLoad = pyqtSignal()

    def __init__(self, song, jack_client, app):
        QObject.__init__(self)
        super(Gui, self).__init__()
        self._jack_client = jack_client
        self.sr = jack_client.samplerate
        self.app = app
        self.setupUi(self)
        self.is_learn_device_mode = False
        self.queue_out, self.queue_in = Queue(), Queue()
        self.updateUi.connect(self.update)
        self.readQueueIn.connect(self.readQueue)
        self.current_vol_block = 0
        self.last_clip = None
        self.portListCallback = set()
        self.sync_source = SYNC_SOURCE_JACK

        # Load devices
        self.deviceGroup = QActionGroup(self.menuDevice)
        self.devices = []
        device_settings = QSettings('superboucle', 'devices')
        if ((device_settings.contains('devices')
             and device_settings.value('devices'))):
            for raw_device in device_settings.value('devices'):
                self.devices.append(Device(pickle.loads(raw_device)))
        else:
            self.devices.append(Device({'name': 'No Device'}))
        self.updateDevices()
        self.deviceGroup.triggered.connect(self.onDeviceSelect)

        self.settings = QSettings('superboucle', 'session')
        # Qsetting appear to serialize empty lists as @QInvalid
        # which is then read as None :(

        # Load playlist
        self.playlist = self.settings.value('playlist', []) or []
        # Load paths
        self.paths_used = self.settings.value('paths_used', {})

        self.auto_connect = self.settings.value('auto_connect',
                                                'true') == "true"

        # Load song
        self.port_by_name = {}
        self.midi_port_by_name = {}
        self.initUI(song)

        self.actionNew.triggered.connect(self.onActionNew)
        self.actionOpen.triggered.connect(self.onActionOpen)
        self.actionSave.triggered.connect(self.onActionSave)
        self.actionSave_As.triggered.connect(self.onActionSaveAs)
        self.actionQuit.triggered.connect(self.onActionQuit)
        self.actionAdd_Device.triggered.connect(self.onAddDevice)
        self.actionManage_Devices.triggered.connect(self.onManageDevice)
        self.actionPlaylist_Editor.triggered.connect(self.onPlaylistEditor)
        self.actionScene_Manager.triggered.connect(self.onSceneManager)
        self.actionPort_Manager.triggered.connect(PortManager.__init__)
        self.actionFullScreen.triggered.connect(self.onActionFullScreen)
        self.master_volume.valueChanged.connect(self.onMasterVolumeChange)
        self.bpm.valueChanged.connect(self.onBpmChange)
        self.beat_per_bar.valueChanged.connect(self.onBeatPerBarChange)
        self.rewindButton.clicked.connect(self.onRewindClicked)
        self.playButton.clicked.connect(self._jack_client.transport_start)
        self.pauseButton.clicked.connect(self._jack_client.transport_stop)
        self.gotoButton.clicked.connect(self.onGotoClicked)
        self.recordButton.clicked.connect(self.onRecord)

        self.blktimer = QTimer()
        self.blktimer.state = False
        self.blktimer.timeout.connect(self.toggleBlinkButton)
        self.blktimer.start(self.BLINK_DURATION)

        self.disptimer = QTimer()
        self.disptimer.start(self.PROGRESS_PERIOD)
        self.disptimer.timeout.connect(self.updateProgress)

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

        # first pass without removing old ports
        self.updateJackPorts(song, remove_ports=False)
        self.song = song
        # second pass with removing
        self.updateJackPorts(song, remove_ports=True)

        self.master_volume.setValue(int(song.volume * 256))
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

        self.setWindowTitle("Super Boucle - {}"
                            .format(song.file_name or "Empty Song"))

        if self.song.initial_scene in self.song.scenes:
            self.song.loadScene(self.song.initial_scene)
        self.update()
        self.songLoad.emit()

    def openSongFromDisk(self, file_name):
        self._jack_client.transport_stop()
        self._jack_client.transport_locate(0)

        self.setEnabled(False)
        message = QMessageBox(self)
        message.setWindowTitle("Loading ....")
        message.setText("Reading Files, please wait ...")
        message.show()
        self.initUI(Song(file=file_name))
        message.close()
        self.setEnabled(True)

    def closeEvent(self, event):
        device_settings = QSettings('superboucle', 'devices')
        device_settings.setValue('devices',
                                 [pickle.dumps(x.mapping)
                                  for x in self.devices])
        self.settings.setValue('playlist', self.playlist)
        self.settings.setValue('paths_used', self.paths_used)
        self.settings.setValue('auto_connect', self.auto_connect)

    def onStartStopClicked(self):
        clip = self.sender().parent().parent().clip
        self.startStop(clip.x, clip.y)

    def startStop(self, x, y):
        clip = self.btn_matrix[x][y].clip
        if clip is None:
            return
        if self.song.is_record:
            self.song.is_record = False
            self.updateRecordBtn()
            # calculate buffer size
            if self.sync_source == SYNC_SOURCE_JACK:
                _, position = self._jack_client.transport_query()
                bpm = position['beats_per_minute']
            elif self.sync_source == SYNC_SOURCE_MIDI:
                bpm = self.bpm.value()
            beat_sample = self.bpm_to_beat_period(bpm)
            print("FPS: %s BPM: %s BS: %s" % (self.sr, bpm, beat_sample))
            size = int((60 / bpm) * clip.beat_diviser * self.sr)
            self.song.init_record_buffer(clip, 2, size, self.sr, beat_sample)
            # set frame offset based on jack block size
            #clip.frame_offset = self._jack_client.blocksize
            clip.state = Clip.PREPARE_RECORD
            self.recordButton.setStyleSheet(self.RECORD_DEFAULT)
        else:
            self.song.toggle(clip.x, clip.y)
        self.update()

    def onEdit(self):
        cell = self.sender().parent().parent()
        if cell.clip:
            if isinstance(cell.clip, MidiClip):
                EditMidiDialog(self, cell.clip)
            else:
                EditClipDialog(self, self.song, cell)

    def onAddClipClicked(self):
        cell = self.sender().parent().parent()
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            cell.setClip(cell.openClip())
        else:
            AddClipDialog(self, cell)

    def onMasterVolumeChange(self):
        self.song.volume = (self.master_volume.value() / 256)

    def onBpmChange(self):
        self.song.bpm = self.bpm.value()

    def onBeatPerBarChange(self):
        self.song.beat_per_bar = self.beat_per_bar.value()

    def onGotoClicked(self):
        state, position = self._jack_client.transport_query()
        new_position = (position['beats_per_bar']
                        * (self.gotoTarget.value() - 1)
                        * position['frame_rate']
                        * (60 / position['beats_per_minute']))
        self._jack_client.transport_locate(int(round(new_position, 0)))

    def onRecord(self):
        self.song.is_record = not self.song.is_record
        self.updateRecordBtn()

    def updateRecordBtn(self):
        if not self.song.is_record:
            self.recordButton.setStyleSheet(self.RECORD_DEFAULT)
        if self.device.record_btn:
            (msg_type, channel, pitch, velocity) = self.device.record_btn
            if self.song.is_record:
                color = self.device.blink_amber_vel
            else:
                color = self.device.black_vel
            self.queue_out.put(((msg_type << 4) + channel, pitch, color))

    def onRewindClicked(self):
        self._jack_client.transport_locate(0)

    def removePort(self, name):
        if name != Clip.DEFAULT_OUTPUT:
            self.song.outputsPorts.remove(name)
            for c in self.song.clips:
                if c.output == name:
                    c.output = Clip.DEFAULT_OUTPUT
            self.updateJackPorts(self.song)
            self.portListUpdate()

    def updateJackPorts(self, song, remove_ports=True):
        '''Update jack port based on clip output settings
        update dict containing ports with shortname as key'''

        song.updateJackPorts(remove_ports)
        self.updatePorts.emit()

    def registerPortListUpdateCallback(self, callback):
        self.portListCallback.add(callback)

    def unregisterPortListUpdateCallback(self, callback):
        self.portListCallback.remove(callback)

    def portListUpdate(self):
        for l in self.portListCallback:
            l()

    def onActionNew(self):
        NewSongDialog(self)

    def getOpenFileName(self, title, file_type, parent=None,
                        dialog=QFileDialog.getOpenFileName):
        path = self.paths_used.get(file_type, expanduser('~'))
        file_name, a = dialog(parent or self, title, path, file_type)
        if a and file_name:
            if isinstance(file_name, list):
                self.paths_used[file_type] = dirname(file_name[0])
            else:
                self.paths_used[file_type] = dirname(file_name)
        return file_name, a

    def getSaveFileName(self, *args):
        return self.getOpenFileName(*args, dialog=QFileDialog.getSaveFileName)

    def onActionOpen(self):
        file_name, a = self.getOpenFileName('Open Song',
                                            'Super Boucle Song (*.sbs)')
        if a and file_name and self.checkFileExists(file_name):
            self.openSongFromDisk(file_name)
        else:
            QMessageBox.critical(self, "File not found",
                                 "File %s does not seem to exist" % file_name)

    def checkFileExists(self, file_name):
        return isfile(file_name)

    def onActionSave(self):
        if self.song.file_name:
            self.song.save()
        else:
            self.onActionSaveAs()

    def onActionSaveAs(self):
        file_name, a = self.getSaveFileName('Save Song',
                                            'Super Boucle Song (*.sbs)')

        if file_name:
            file_name = verify_ext(file_name, 'sbs')
            self.song.file_name = file_name
            self.song.save()
            print("File saved to : {}".format(self.song.file_name))

    def onActionQuit(self):
        self.app.quit()

    def onAddDevice(self):
        self.learn_device = LearnDialog(self, self.addDevice)
        self.is_learn_device_mode = True

    def onManageDevice(self):
        ManageDialog(self)

    def onPlaylistEditor(self):
        PlaylistDialog(self)

    def onSceneManager(self):
        SceneManager(self)

    def onPortManager(self):
        PortManager(self)

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
                        self.btn_matrix[x][y].setColor(state)
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
                    # else:
                    # print("Invalid message length")
        except Empty:
            pass

    def processNote(self, msg_type, channel, pitch, vel):

        btn_id = (msg_type,
                  channel,
                  pitch,
                  vel)
        btn_id_vel = (msg_type, channel, pitch, -1)
        ctrl_key = (msg_type, channel, pitch)

        # master volume
        if ctrl_key == self.device.master_volume_ctrl:
            self.song.master_volume = vel / 127
            (self.master_volume
             .setValue(int(self.song.master_volume * 256)))
        elif self.device.play_btn in [btn_id, btn_id_vel]:
            self._jack_client.transport_start()
        elif self.device.pause_btn in [btn_id, btn_id_vel]:
            self._jack_client.transport_stop()
        elif self.device.rewind_btn in [btn_id, btn_id_vel]:
            self.onRewindClicked()
        elif self.device.goto_btn in [btn_id, btn_id_vel]:
            self.onGotoClicked()
        elif self.device.record_btn in [btn_id, btn_id_vel]:
            self.onRecord()
        elif ctrl_key in self.device.ctrls:
            try:
                ctrl_index = self.device.ctrls.index(ctrl_key)
                clip = (self.song.clips_matrix
                        [ctrl_index]
                        [self.current_vol_block])
                if clip:
                    clip.volume = vel / 127
                    if self.last_clip == clip:
                        self.clip_volume.setValue(self.last_clip.volume * 256)
            except KeyError:
                pass
        elif (btn_id in self.device.scene_buttons
              or btn_id_vel in self.device.scene_buttons):
            try:
                scene_id = self.device.scene_buttons.index(btn_id)
            except ValueError:
                scene_id = self.device.scene_buttons.index(btn_id_vel)

            try:
                self.song.loadSceneId(scene_id)
                self.update()
            except IndexError:
                print('cannot load scene {} - there are only {} scenes.'
                      ''.format(scene_id, len(self.song.scenes)))

        elif (btn_id in self.device.block_buttons
              or btn_id_vel in self.device.block_buttons):
            try:
                self.current_vol_block = (
                    self.device.block_buttons.index(btn_id))
            except ValueError:
                self.current_vol_block = (
                    self.device.block_buttons.index(btn_id_vel))
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
            x, y = -1, -1
            try:
                x, y = self.device.getXY(btn_id)
            except IndexError:
                pass
            except KeyError:
                try:
                    x, y = self.device.getXY(btn_id_vel)
                except KeyError:
                    pass

            if (x >= 0 and y >= 0):
                self.startStop(x, y)

    def toggleBlinkButton(self):
        for line in self.btn_matrix:
            for btn in line:
                if btn.blink:
                    if self.blktimer.state:
                        btn.setStyleSheet(btn.color)
                    else:
                        btn.setStyleSheet(self.DEFAULT)
        if self.song.is_record:
            if self.blktimer.state:
                self.recordButton.setStyleSheet(self.RECORD_BLINK)
            else:
                self.recordButton.setStyleSheet(self.RECORD_DEFAULT)

        self.blktimer.state = not self.blktimer.state

    def updateProgress(self):
        if self.sync_source == SYNC_SOURCE_JACK:
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
                if btn.clip:
                    value = btn.clip.getPos() * 97
                    btn.clip_position.setValue(int(value))
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


    def bpm_to_tick_period(self, bpm):
        return (60 * self.sr) / (bpm * 24)

    def tick_period_to_bpm(self, period):
        return (60 * self.sr) / (period * 24)

    def bpm_to_beat_period(self, bpm):
        return (60 * self.sr) / (bpm)

    def beat_period_to_bpm(self, beat_period):
        return (60 * self.sr) / (beat_period)
