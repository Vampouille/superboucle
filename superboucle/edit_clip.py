import numpy as np
import soundfile as sf
from PyQt5.QtWidgets import QDialog, QMessageBox
from superboucle.add_port import AddPortDialog
from superboucle.edit_clip_ui import Ui_Dialog
from superboucle.clip import verify_ext


class EditClipDialog(QDialog, Ui_Dialog):
    ADD_PORT_LABEL = "Add new Port..."

    def __init__(self, parent, song, clip):
        super(EditClipDialog, self).__init__(parent)
        self.gui = parent
        self.gui.registerPortListUpdateCallback(self.updatePortList)
        self.setupUi(self)
        self.song = song
        self.clip = clip
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
        self.show()

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
        if self.clip and self.clip.audio_file:
            audio_file = self.clip.audio_file
            absolute_val = np.absolute(self.song.data[audio_file])
            current_level = np.ndarray.max(absolute_val)
            self.song.data[audio_file][:] *= 1 / current_level

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
