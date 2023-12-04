from PyQt5.QtWidgets import QDialog, QMessageBox
from superboucle.set_tempo_ui import Ui_Dialog
from superboucle.clip import verify_ext


class SetTempoDialog(QDialog, Ui_Dialog):

    def __init__(self, parent):
        super(SetTempoDialog, self).__init__(parent)
        self.edit_clip = parent
        self.setupUi(self)
        self.sr = self.edit_clip.gui._jack_client.samplerate
        self.bpm.valueChanged.connect(self.onBPMChanged)
        self.sample_per_beat.valueChanged.connect(self.onSamplePerBeatChanged)
        self.set_current_button.clicked.connect(self.onSetCurrentTempo)
        self.forgot_button.clicked.connect(self.onForgotTempo)
        self.buttonBox.accepted.connect(self.onOk)
        self.buttonBox.rejected.connect(self.onCancel)

    def onSamplePerBeatChanged(self):
        self.bpm.setValue(60 / (self.sr * self.sample_per_beat.value()))

    def onBPMChanged(self):
        self.sample_per_beat.setValue(self.sr / (self.bpm.value() / 60))

    def onSetCurrentTempo(self):
        bpm = self.edit_clip.gui.bpm.value()
        self.bpm.setValue(bpm)
        self.sample_per_beat.setValue(self.sr/(bpm/60))

    def onForgotTempo(self):
        self.bpm.setValue(0.0)
        self.sample_per_beat.setValue(0)

    def onOk(self):
        beat_sample = self.sample_per_beat.value()
        self.edit_clip.clip.audio_file.beat_sample = beat_sample if beat_sample != 0 else None
        if self.edit_clip.clip.audio_file.beat_sample is not None:
            self.edit_clip.stretch_mode_resample.setEnabled(True)
            self.edit_clip.stretch_mode_timestretch.setEnabled(True)
            self.edit_clip.stretch_mode_resample.setToolTip("")
            self.edit_clip.stretch_mode_timestretch.setToolTip("")
        self.accept()

    def onCancel(self):
        self.reject()
