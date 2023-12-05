import numpy as np
import soundfile as sf
from PyQt5.QtWidgets import QDialog, QMessageBox
from superboucle.add_port import AddPortDialog
from superboucle.edit_clip_ui import Ui_Dialog
from superboucle.clip import verify_ext
from superboucle.set_tempo import SetTempoDialog


class EditClipDialog(QDialog, Ui_Dialog):
    ADD_PORT_LABEL = "Add new Port..."

    COLORS = {"Creating": "background-color: #df8b67",
              "Next": "background-color: #df67a6",
              "Active": "background-color: rgb(223, 27, 130)",
              "Inactive": ""}
    NOT_AVAILABLE = "BPM on original is mandatory, please first set tempo"


    def __init__(self, parent, song, clip):
        super(EditClipDialog, self).__init__(parent)
        self.gui = parent
        self.gui.registerPortListUpdateCallback(self.updatePortList)
        self.setupUi(self)
        self.song = song
        self.clip = clip
        self.clip.registerAudioChange(self.updateAudioDesc)
        self.clip_name.setText(clip.name)
        self.clip_name.textChanged.connect(self.onClipNameChange)
        self.setWindowTitle(clip.name)
        self.clip_volume.setValue(int(clip.volume * 256))
        self.clip_volume.knobRadius = 3
        self.clip_volume.valueChanged.connect(self.onClipVolumeChange)
        self.beat_diviser.valueChanged.connect(self.onBeatDiviserChange)
        self.beat_diviser.setValue(clip.beat_diviser)
        self.frame_offset.setValue(clip.frame_offset)
        self.frame_offset.valueChanged.connect(self.onFrameOffsetChange)
        self.beat_offset.setValue(clip.beat_offset)
        self.beat_offset.valueChanged.connect(self.onBeatOffsetChange)
        self.set_tempo.clicked.connect(self.onSetTempo)
        if clip.audio_file == None or clip.audio_file.beat_sample == None:
            self.stretch_mode_resample.setEnabled(False)
            self.stretch_mode_timestretch.setEnabled(False)
            self.stretch_mode_resample.setToolTip(EditClipDialog.NOT_AVAILABLE)
            self.stretch_mode_timestretch.setToolTip(EditClipDialog.NOT_AVAILABLE)
        if clip.stretch_mode == "disable":
            self.stretch_mode_disable.setChecked(True)
        if clip.stretch_mode == "resample":
            self.stretch_mode_resample.setChecked(True)
        if clip.stretch_mode == "timestretch":
            self.stretch_mode_timestretch.setChecked(True)
        self.stretch_mode_disable.clicked.connect(self.onStretchModeDisable)
        self.stretch_mode_resample.clicked.connect(self.onStretchModeResample)
        self.stretch_mode_timestretch.clicked.connect(self.onStretchModeTimestretch)
        self.output.clear()
        self.output.addItems(song.outputsPorts)
        self.output.addItem(EditClipDialog.ADD_PORT_LABEL)
        self.output.setCurrentText(clip.output)
        self.output.activated.connect(self.onOutputChange)
        self.mute_group.setValue(clip.mute_group)
        self.mute_group.valueChanged.connect(self.onMuteGroupChange)
        self.reverseButton.clicked.connect(self.onReverseClip)
        self.normalizeButton.clicked.connect(self.onNormalizeClip)
        self.exportButton.clicked.connect(self.onExportClip)
        self.deleteButton.clicked.connect(self.onDeleteClipClicked)
        self.save_orig.clicked.connect(self.onSaveOrig)
        self.save_a.clicked.connect(self.onSaveA)
        self.save_b.clicked.connect(self.onSaveB)
        self.refreshAudioDesc()
        self.show()


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

    def onStretchModeResample(self):
        self.clip.stretch_mode = "resample"

    def onStretchModeTimestretch(self):
        self.clip.stretch_mode = "time"

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

    def onFinished(self):
        self.gui.unregisterPortListUpdateCallback(self.updatePortList)

    def generate_audio_desc(self, wf):
        if wf is None:
            return "-"
        if wf.beat_sample is None:
            return "- BPM"
        return "%s BPM" % round(self.gui.beat_period_to_bpm(wf.beat_sample), 2)

    def updateAudioDesc(self, a_b, msg):
        self.audio_0.setText(self.generate_audio_desc(self.clip.audio_file))
        self.audio_a.setText(self.generate_audio_desc(self.clip.audio_file_a))
        self.audio_b.setText(self.generate_audio_desc(self.clip.audio_file_b))
        labels = [self.audio_0_label, self.audio_a_label, self.audio_b_label]
        for l in labels:
            l.setStyleSheet("")
        labels[a_b].setStyleSheet("background-color: %s" % self.COLORS[msg])
        labels[a_b].repaint()

    def refreshAudioDesc(self):
        self.audio_0.setText(self.generate_audio_desc(self.clip.audio_file))
        self.audio_a.setText(self.generate_audio_desc(self.clip.audio_file_a))
        self.audio_b.setText(self.generate_audio_desc(self.clip.audio_file_b))
        labels = [self.audio_0_label, self.audio_a_label, self.audio_b_label]
        for l in labels:
            l.setStyleSheet("")
        labels[self.clip.audio_file_id].setStyleSheet("%s" % self.COLORS['Active'])
