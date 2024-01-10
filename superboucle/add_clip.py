from PyQt5.QtWidgets import QDialog, QButtonGroup
from superboucle.add_clip_ui import Ui_Dialog
from superboucle.clip import Clip
from superboucle.clip_midi import MidiClip


class AddClipDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, cell):
        super(AddClipDialog, self).__init__(parent)
        self.gui = parent
        self.cell = cell
        self.type = None
        self.setupUi(self)
        group = QButtonGroup(self)
        group.addButton(self.audioLoadButton)
        group.addButton(self.audioNewButton)
        group.addButton(self.midiLoadButton)
        group.addButton(self.midiNewButton)
        self.accepted.connect(self.onOk)
        self.show()

    def onOk(self):

        new_clip = None
        if self.audioLoadButton.isChecked():
            new_clip = self.cell.openClip()
        elif self.audioNewButton.isChecked():
            new_clip = Clip(audio_file=None, name='audio-%02d' % len(self.gui.song.clips))
        elif self.midiNewButton.isChecked():
            new_clip = MidiClip('midi-%02d' % len(self.gui.song.clips), 16, 0)

        if new_clip:
            self.cell.setClip(new_clip)
