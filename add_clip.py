from PyQt5.QtWidgets import QDialog
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
            new_clip = self.cell.openClip()

        elif self.type == 'use':
            wav_id = self.fileList.currentText()
            new_clip = Clip(basename(wav_id))

        elif self.type == 'empty':
            new_clip = Clip(audio_file=None,
                            name='audio-%02d' % len(self.gui.song.clips))

        if new_clip:
            self.cell.setClip(new_clip)
