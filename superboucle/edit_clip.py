import numpy as np
import soundfile as sf
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
from superboucle.add_port import AddPortDialog
from superboucle.edit_clip_ui import Ui_Dialog
from superboucle.set_tempo import SetTempoDialog
from superboucle.song import verify_ext


class EditClipDialog(QDialog, Ui_Dialog):
    ADD_PORT_LABEL = "Add new Port..."

    COLORS = {"Creating": "background-color: #df8b67",
              "Next": "background-color: #df67a6",
              "Active": "background-color: rgb(223, 27, 130)",
              "Inactive": ""}
    NOT_AVAILABLE = "BPM on original is mandatory, please first set tempo or record"

    changeActiveSignal = pyqtSignal(int, int)
    updateAudioDescSignal = pyqtSignal(int)

    def __init__(self, parent, song, cell):
        super(EditClipDialog, self).__init__(parent)
        self.gui = parent
        self.gui.registerPortListUpdateCallback(self.updatePortList)
        self.setupUi(self)
        self.song = song
        self.clip = cell.clip
        self.cell = cell
        self.clip.edit_clip = self
        self.clip_name.setText(self.clip.name)
        self.clip_name.textChanged.connect(self.onClipNameChange)
        self.setWindowTitle(self.clip.name)
        self.clip_volume.setValue(int(self.clip.volume * 256))
        self.clip_volume.knobRadius = 3
        self.clip_volume.valueChanged.connect(self.onClipVolumeChange)
        self.beat_diviser.valueChanged.connect(self.onBeatDiviserChange)
        self.beat_diviser.setValue(self.clip.beat_diviser)
        self.frame_offset.setValue(self.clip.frame_offset)
        self.frame_offset.valueChanged.connect(self.onFrameOffsetChange)
        self.beat_offset.setValue(self.clip.beat_offset)
        self.beat_offset.valueChanged.connect(self.onBeatOffsetChange)
        self.set_tempo.clicked.connect(self.onSetTempo)
        if self.clip.audio_file == None or self.clip.audio_file.beat_sample == None:
            self.stretch_mode_resample.setEnabled(False)
            self.stretch_mode_timestretch.setEnabled(False)
            self.stretch_mode_resample.setToolTip(EditClipDialog.NOT_AVAILABLE)
            self.stretch_mode_timestretch.setToolTip(EditClipDialog.NOT_AVAILABLE)
        if self.clip.stretch_mode == "disable":
            self.stretch_mode_disable.setChecked(True)
        if self.clip.stretch_mode == "resample":
            self.stretch_mode_resample.setChecked(True)
        if self.clip.stretch_mode == "timestretch":
            self.stretch_mode_timestretch.setChecked(True)
        self.stretch_mode_disable.clicked.connect(self.onStretchModeDisable)
        self.stretch_mode_resample.clicked.connect(self.onStretchModeResample)
        self.stretch_mode_timestretch.clicked.connect(self.onStretchModeTimestretch)
        self.output.clear()
        self.output.addItems(song.outputsPorts)
        self.output.addItem(EditClipDialog.ADD_PORT_LABEL)
        self.output.setCurrentText(self.clip.output)
        self.output.activated.connect(self.onOutputChange)
        self.mute_group.setValue(self.clip.mute_group)
        self.mute_group.valueChanged.connect(self.onMuteGroupChange)
        self.reverseButton.clicked.connect(self.onReverseClip)
        self.normalizeButton.clicked.connect(self.onNormalizeClip)
        self.exportButton.clicked.connect(self.onExportClip)
        self.deleteButton.clicked.connect(self.onDeleteClipClicked)
        self.save_orig.clicked.connect(self.onSaveOrig)
        self.save_a.clicked.connect(self.onSaveA)
        self.save_b.clicked.connect(self.onSaveB)
        self.labels = [self.audio_0_label, self.audio_a_label, self.audio_b_label]
        self.refreshAudioDesc()
        self.changeActiveSignal.connect(self.changeActive)
        self.updateAudioDescSignal.connect(self.updateDesc)

        self.show()
        self.cell.edit.setEnabled(False)


    def onSaveOrig(self):
        self.saveWF(self.clip.audio_file, "Original audio")
    
    def onSaveA(self):
        self.saveWF(self.clip.audio_file_a, "Audio A")
    
    def onSaveB(self):
        self.saveWF(self.clip.audio_file_b, "Audio B")
    
    def saveWF(self, wf, desc):
        file_name, a = self.gui.getSaveFileName("Save %s" % desc,
                                               'Wav file (*.wav)')  
        if file_name:
            file_name = verify_ext(file_name, 'wav')
            sf.write(file_name, wf.data, wf.sr)

    def onClipNameChange(self):
        self.clip.name = self.clip_name.text()
        cell = self.gui.btn_matrix[self.clip.x][self.clip.y]
        cell.clip_name.setText(self.clip.name)
        self.setWindowTitle(self.clip.name)

    def onClipVolumeChange(self):
        self.clip.volume = self.clip_volume.value() / 256

    def onBeatDiviserChange(self):
        self.clip.beat_diviser = self.beat_diviser.value()

    def onFrameOffsetChange(self):
        self.clip.frame_offset = self.frame_offset.value()

    def onBeatOffsetChange(self):
        self.clip.beat_offset = self.beat_offset.value()

    def onSetTempo(self):
        SetTempoDialog(self)

    def onStretchModeDisable(self):
        self.clip.stretch_mode = "disable"
        self.clip.audio_file_next_id = 0
        self.setColor(0, "Next")

    def onStretchModeResample(self):
        self.clip.stretch_mode = "resample"
        #self.clip.changeBeatSample(self.clip.getBeatSample())

    def onStretchModeTimestretch(self):
        self.clip.stretch_mode = "timestretch"
        #self.clip.changeBeatSample(self.clip.getBeatSample())

    def onOutputChange(self):
        new_port = self.output.currentText()
        if new_port == EditClipDialog.ADD_PORT_LABEL:
            AddPortDialog(self, self.addPortOkCallback, self.addPortCancelCallback)
        else:
            self.clip.output = new_port

    def updatePortList(self):
        self.output.clear()
        self.output.addItems(self.song.outputsPorts)
        self.output.addItem(EditClipDialog.ADD_PORT_LABEL)
        self.output.setCurrentText(self.clip.output)

    def addPortOkCallback(self, name):
        self.song.outputsPorts.add(name)
        self.clip.output = name
        self.gui.updateJackPorts(self.song)
        self.gui.portListUpdate()

    def addPortCancelCallback(self):
        self.output.setCurrentText(self.clip.output)

    def onMuteGroupChange(self):
        self.clip.mute_group = self.mute_group.value()

    def onReverseClip(self):
        if self.clip and self.clip.audio_file:
            audio_file = self.clip.audio_file
            self.song.data[audio_file] = self.song.data[audio_file][::-1]

    def onNormalizeClip(self):
        c = self.clip
        if c:
            if c.audio_file:
                c.audio_file.normalize()
            if c.audio_file_a:
                c.audio_file_a.normalize()
            if c.audio_file_b:
                c.audio_file_b.normalize()

    def onExportClip(self):
        if self.clip and self.clip.audio_file:
            audio_file = self.clip.audio_file
            file_name, a = self.getSaveFileName(
                "Export Clip : %s" % self.clip.name, "WAVE (*.wav)"
            )

            if file_name:
                file_name = verify_ext(file_name, "wav")
                sf.write(
                    file_name,
                    self.song.data[audio_file],
                    self.song.samplerate[audio_file],
                    subtype=sf.default_subtype("WAV"),
                    format="WAV",
                )

    def onDeleteClipClicked(self):
        if self.clip:
            response = QMessageBox.question(
                self, "Delete Clip ?", ("Are you sure " "to delete the clip ?")
            )
            if response == QMessageBox.Yes:
                self.song.removeClip(self.clip)
                self.gui.initUI(self.song)
                self.reject()

    def closeEvent(self, event):
        self.gui.unregisterPortListUpdateCallback(self.updatePortList)
        self.cell.edit.setEnabled(True)
        self.clip.edit_clip = None

    def generate_audio_desc(self, wf):
        if wf is None:
            return "-"
        if wf.beat_sample is None:
            return "- BPM"
        effect = ""
        if wf.effect == "timestretch":
            effect = "T/S"
        elif wf.effect == "resample":
            effect = "R"
        return "%s BPM %s" % (round(self.gui.beat_period_to_bpm(wf.beat_sample), 2), effect)
        

    # TODO : remove ?
    def updateAudioDesc(self, a_b, msg):
        print("updateAudioDesc(%s, %s)..." % (a_b, msg), end="")
        self.audio_0.setText(self.generate_audio_desc(self.clip.audio_file))
        self.audio_a.setText(self.generate_audio_desc(self.clip.audio_file_a))
        self.audio_b.setText(self.generate_audio_desc(self.clip.audio_file_b))
        #for l in labels:
        #    l.setStyleSheet("")
        self.labels[a_b].setStyleSheet(self.COLORS[msg])
        #labels[a_b].repaint()
        print("OK")

    # TODO : remove ?
    def refreshAudioDesc(self):
        self.audio_0.setText(self.generate_audio_desc(self.clip.audio_file))
        self.audio_a.setText(self.generate_audio_desc(self.clip.audio_file_a))
        self.audio_b.setText(self.generate_audio_desc(self.clip.audio_file_b))
        #for l in labels:
        #    l.setStyleSheet("")
        self.labels[self.clip.audio_file_id].setStyleSheet(self.COLORS['Active'])
    
    def setColor(self, index, msg):
        self.labels[index].setStyleSheet(self.COLORS[msg])
    
    def updateDesc(self, index):
        if index == 0:
            self.audio_0.setText(self.generate_audio_desc(self.clip.audio_file))
            if self.clip.audio_file is not None and self.clip.audio_file.beat_sample:
                self.stretch_mode_resample.setEnabled(True)
                self.stretch_mode_timestretch.setEnabled(True)
                self.stretch_mode_resample.setToolTip("")
                self.stretch_mode_timestretch.setToolTip("")
        elif index == 1:
            self.audio_a.setText(self.generate_audio_desc(self.clip.audio_file_a))
        elif index == 2:
            self.audio_b.setText(self.generate_audio_desc(self.clip.audio_file_b))
    
    def changeActive(self, inactive, active):
        self.labels[inactive].setStyleSheet(self.COLORS["Inactive"])
        self.labels[active].setStyleSheet(self.COLORS["Active"])
