from PyQt5.QtWidgets import QDialog, QFileDialog
from os.path import expanduser
import numpy as np
import soundfile as sf
from add_clip_ui import Ui_Dialog
from clip import Clip, basename


class AddClipDialog(QDialog, Ui_Dialog):

    def __init__(self, parent, cell):
        super(AddClipDialog, self).__init__(parent)
        self.gui = parent
        self.cell = cell
        self.type = None
        self.setupUi(self)

        self.newButton.clicked.connect(self.onNew)
        self.useButton.clicked.connect(self.onUse)
        self.emptyButton.clicked.connect(self.onEmpty)
        self.accepted.connect(self.onOk)

        for wav_id in self.gui.song.data:
            self.fileList.addItem(wav_id)

        self.show()

    def onNew(self):
        self.type = 'new'

    def onUse(self):
        self.type = 'use'

    def onEmpty(self):
        self.type = 'empty'

    def onOk(self):

        new_clip = None

        if self.type == 'new':
            audio_file, a = QFileDialog.getOpenFileName(self,
                                                        'Open Clip file',
                                                        expanduser("~"),
                                                        'All files (*.*)')
            if audio_file:
                wav_id = basename(audio_file)
                if wav_id in self.gui.song.data:
                    i = 0
                    while "%s-%02d" % (wav_id, i) in self.gui.song.data:
                        i += 1
                    wav_id = "%s-%02d" % (wav_id, i)

                data, samplerate = sf.read(audio_file, dtype=np.float32)
                self.gui.song.data[wav_id] = data
                self.gui.song.samplerate[wav_id] = samplerate

                new_clip = Clip(basename(wav_id))

        elif self.type == 'use':
            wav_id = self.fileList.currentText()
            new_clip = Clip(basename(wav_id))

        elif self.type == 'empty':
            new_clip = Clip(audio_file=None,
                            name='audio-%02d' % len(self.gui.song.clips))

        if new_clip:
            self.cell.clip = new_clip
            self.cell.clip_name.setText(new_clip.name)
            self.cell.start_stop.clicked.connect(self.gui.onStartStopClicked)
            self.cell.edit.setText("Edit")
            self.cell.edit.clicked.disconnect(self.gui.onAddClipClicked)
            self.cell.edit.clicked.connect(self.gui.onEdit)
            self.cell.start_stop.setEnabled(True)
            self.cell.clip_position.setEnabled(True)
            self.gui.song.addClip(new_clip,
                                  self.cell.pos_x,
                                  self.cell.pos_y)
            self.gui.update()
