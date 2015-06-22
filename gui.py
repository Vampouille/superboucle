#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Gui
"""
from PyQt5.QtWidgets import (QWidget, QMainWindow, QFileDialog,
                             QAction, QActionGroup, QMessageBox, QApplication)
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QSettings, Qt

from clip import Clip, load_song_from_file, verify_ext, basename
from gui_ui import Ui_MainWindow
from cell_ui import Ui_Cell
from learn import LearnDialog
from manage import ManageDialog
from playlist import PlaylistDialog, getSongs
from port_manager import PortManager
from new_song import NewSongDialog
from add_clip import AddClipDialog
from threading import Event
from device import Device
import struct
from queue import Queue, Empty
import pickle
from os.path import expanduser, dirname
import numpy as np
import soundfile as sf

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

        self.gui = parent
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

    def setClip(self, new_clip):
        self.clip = new_clip
        self.clip_name.setText(new_clip.name)
        self.start_stop.clicked.connect(self.gui.onStartStopClicked)
        self.edit.setText("Edit")
        self.edit.clicked.disconnect(self.gui.onAddClipClicked)
        self.edit.clicked.connect(self.gui.onEdit)
        self.start_stop.setEnabled(True)
        self.clip_position.setEnabled(True)
        self.gui.song.addClip(new_clip, self.pos_x, self.pos_y)
        self.gui.updatePorts.emit()
        self.gui.update()

    def openClip(self):
        audio_file, a = self.gui.getOpenFileName('Open Clip',
                                                 'All files (*.*)', self)
        if audio_file and a:
            wav_id = basename(audio_file)
            if wav_id in self.gui.song.data:
                i = 0
                while "%s-%02d" % (wav_id, i) in self.gui.song.data:
                    i += 1
                wav_id = "%s-%02d" % (wav_id, i)

            data, samplerate = sf.read(audio_file, dtype=np.float32)
            self.gui.song.data[wav_id] = data
            self.gui.song.samplerate[wav_id] = samplerate

            return Clip(basename(wav_id))


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

        self.ports_initialised = Event()
        self.ports_initialised.clear()

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

        # TODO: find a nicer way to store settings - discussion desirable.
        # Load playlist
        self.settings = QSettings('superboucle', 'session')
        # Qsetting appear to serialize empty lists as @QInvalid which is then read as None :(
        self.playlist = getSongs(self.settings.value('playlist', []) or [])
        self.paths_used = self.settings.value('paths_used', {})

        self.auto_connect = self.settings.value('auto_connect',
                                                'true') == "true"


        # Load song
        self.output_ports_by_name = {}
        self.port_names_by_output = {}
        self.initUI(song)

        self.actionNew.triggered.connect(self.onActionNew)
        self.actionOpen.triggered.connect(self.onActionOpen)
        self.actionSave.triggered.connect(self.onActionSave)
        self.actionSave_As.triggered.connect(self.onActionSaveAs)
        self.actionAdd_Device.triggered.connect(self.onAddDevice)
        self.actionManage_Devices.triggered.connect(self.onManageDevice)
        self.actionPlaylist_Editor.triggered.connect(self.onPlaylistEditor)
        self.actionPort_Manager.triggered.connect(self.onPortManager)
        self.actionFullScreen.triggered.connect(self.onActionFullScreen)
        self.master_volume.valueChanged.connect(self.onMasterVolumeChange)
        self.bpm.valueChanged.connect(self.onBpmChange)
        self.beat_per_bar.valueChanged.connect(self.onBeatPerBarChange)
        self.rewindButton.clicked.connect(self.onRewindClicked)
        self.playButton.clicked.connect(self._jack_client.transport_start)
        self.pauseButton.clicked.connect(self._jack_client.transport_stop)
        self.gotoButton.clicked.connect(self.onGotoClicked)
        self.recordButton.clicked.connect(self.onRecord)
        self.clip_name.textChanged.connect(self.onClipNameChange)
        self.clip_volume.valueChanged.connect(self.onClipVolumeChange)
        self.beat_diviser.valueChanged.connect(self.onBeatDiviserChange)
        self.output.activated.connect(
            self.onOutputChange)  # currentIndexChanged
        self.mute_group.valueChanged.connect(self.onMuteGroupChange)
        self.frame_offset.valueChanged.connect(self.onFrameOffsetChange)
        self.beat_offset.valueChanged.connect(self.onBeatOffsetChange)
        self.revertButton.clicked.connect(self.onRevertClip)
        self.normalizeButton.clicked.connect(self.onNormalizeClip)
        self.exportButton.clicked.connect(self.onExportClip)
        self.deleteButton.clicked.connect(self.onDeleteClipClicked)

        self.blktimer = QTimer()
        self.blktimer.state = False
        self.blktimer.timeout.connect(self.toggleBlinkButton)
        self.blktimer.start(self.BLINK_DURATION)

        self.disptimer = QTimer()
        self.disptimer.start(self.PROGRESS_PERIOD)
        self.disptimer.timeout.connect(self.updateProgress)

        self._jack_client.set_timebase_callback(self.timebase_callback)

        self.updatePorts.connect(self.updatePortEvent)
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

        self.ports_initialised.clear()
        self.song = song
        self.updatePorts.emit()

        self.frame_clip.setEnabled(False)
        self.master_volume.setValue(song.volume * 256)
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

    def updatePortEvent(self):

        self.ports_initialised.clear()
        client = self._jack_client
        print("Outputs ports : ")
        for port in client.outports:
            print(port)

        self.port_names_by_output = {o: list(self.song.channel_names(o)) for o
                                     in self.song.outputs}

        wanted_ports = set(
            c for os in self.port_names_by_output.values() for c in os)

        print("wanted ports:")
        print(wanted_ports)

        # remove unwanted ports
        for port in [port for port in client.outports
                     if port.shortname not in wanted_ports]:
            port.unregister()

        print("Outputs after removing unused ports: ")
        for port in client.outports:
            print(port)

        # create new ports
        current_ports = set(port.shortname for port in client.outports)
        for new_port_name in wanted_ports - current_ports:
            client.outports.register(new_port_name)

        print("Outputs after adding new ports: ")
        for port in client.outports:
            print(port)

        self.output_ports_by_name = {port.shortname: port for port in
                                     client.outports}
        print(self.output_ports_by_name)
        self.ports_initialised.set()

    def closeEvent(self, event):
        settings = QSettings('superboucle', 'devices')
        settings.setValue('devices',
                          [pickle.dumps(x.mapping) for x in self.devices])
        self.settings.setValue('playlist',
                               [song.file_name for song in self.playlist])
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
            state, position = self._jack_client.transport_query()
            bps = position['beats_per_minute'] / 60
            fps = position['frame_rate']
            size = (1 / bps) * clip.beat_diviser * fps
            self.song.init_record_buffer(clip, 2, size, fps)
            # set frame offset based on jack block size
            clip.frame_offset = self._jack_client.blocksize
            clip.state = Clip.PREPARE_RECORD
            self.recordButton.setStyleSheet(self.RECORD_DEFAULT)
        else:
            self.song.toggle(clip.x, clip.y)
        self.update()

    def onEdit(self):
        self.last_clip = self.sender().parent().parent().clip
        if self.last_clip:
            self.frame_clip.setEnabled(True)
            self.clip_name.setText(self.last_clip.name)
            self.frame_offset.setValue(self.last_clip.frame_offset)
            self.beat_offset.setValue(self.last_clip.beat_offset)
            self.beat_diviser.setValue(self.last_clip.beat_diviser)
            ro, op = self.last_clip.output, list(self.song.outputs.keys())
            self.output.clear()
            self.output.insertItems(1, op)
            self.output.setCurrentIndex(op.index(ro))
            self.mute_group.setValue(self.last_clip.mute_group)
            self.clip_volume.setValue(self.last_clip.volume * 256)
            state, position = self._jack_client.transport_query()
            fps = position['frame_rate']
            bps = self.bpm.value() / 60
            if self.bpm.value() and fps:
                size_in_beat = (bps / fps) * self.song.length(self.last_clip)
            else:
                size_in_beat = "No BPM info"
            clip_description = ("Size in sample : %s\nSize in beat : %s"
                                % (self.song.length(self.last_clip),
                                   round(size_in_beat, 1)))

            self.clip_description.setText(clip_description)

    def onAddClipClicked(self):
        cell = self.sender().parent().parent()
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            cell.setClip(cell.openClip())
        else:
            AddClipDialog(self, cell)

    def onRevertClip(self):
        if self.last_clip and self.last_clip.audio_file:
            audio_file = self.last_clip.audio_file
            self.song.data[audio_file] = self.song.data[audio_file][::-1]

    def onNormalizeClip(self):
        if self.last_clip and self.last_clip.audio_file:
            audio_file = self.last_clip.audio_file
            absolute_val = np.absolute(self.song.data[audio_file])
            current_level = np.ndarray.max(absolute_val)
            self.song.data[audio_file][:] *= (1 / current_level)

    def onExportClip(self):
        if self.last_clip and self.last_clip.audio_file:
            audio_file = self.last_clip.audio_file
            file_name, a = self.getSaveFileName(
                'Export Clip : %s' % self.last_clip.name, 'WAVE (*.wav)')

            if file_name:
                file_name = verify_ext(file_name, 'wav')
                sf.write(self.song.data[audio_file], file_name,
                         self.song.samplerate[audio_file],
                         subtype=sf.default_subtype('WAV'),
                         format='WAV')

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

    def onBpmChange(self):
        self.song.bpm = self.bpm.value()

    def onBeatPerBarChange(self):
        self.song.beat_per_bar = self.beat_per_bar.value()

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

    def onClipNameChange(self):
        self.last_clip.name = self.clip_name.text()
        tframe = self.btn_matrix[self.last_clip.x][self.last_clip.y]
        tframe.clip_name.setText(self.last_clip.name)

    def onClipVolumeChange(self):
        self.last_clip.volume = (self.clip_volume.value() / 256)

    def onBeatDiviserChange(self):
        self.last_clip.beat_diviser = self.beat_diviser.value()

    def onOutputChange(self):
        self.last_clip.output = self.output.currentText()
        self.updatePorts.emit()

    def onMuteGroupChange(self):
        self.last_clip.mute_group = self.mute_group.value()

    def onFrameOffsetChange(self):
        self.last_clip.frame_offset = self.frame_offset.value()

    def onBeatOffsetChange(self):
        self.last_clip.beat_offset = self.beat_offset.value()

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
        if a and file_name:
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
        file_name, a = self.getSaveFileName('Save Song',
                                            'Super Boucle Song (*.sbs)')

        if file_name:
            file_name = verify_ext(file_name, 'sbs')
            self.song.file_name = file_name
            self.song.save()
            print("File saved to : {}".format(self.song.file_name))

    def onAddDevice(self):
        self.learn_device = LearnDialog(self, self.addDevice)
        self.is_learn_device_mode = True

    def onManageDevice(self):
        ManageDialog(self)

    def onPlaylistEditor(self):
        PlaylistDialog(self)

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
             .setValue(self.song.master_volume * 256))
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

    def setCellColor(self, x, y, color, blink=False):
        self.btn_matrix[x][y].setStyleSheet(color)
        self.btn_matrix[x][y].blink = blink
        self.btn_matrix[x][y].color = color

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
