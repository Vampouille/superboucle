from PyQt5.QtWidgets import QDialog

from new_song_ui import Ui_Dialog
from clip import Song, getDefaultOutputNames


class NewSongDialog(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(NewSongDialog, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.show()

    def accept(self):
        self.gui.initUI(Song(self.widthSpinBox.value(),
                             self.heightSpinBox.value(),
                             getDefaultOutputNames(self.outputsSpinBox.value())))
        super(NewSongDialog, self).accept()
