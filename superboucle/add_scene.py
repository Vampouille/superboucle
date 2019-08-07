from PyQt5.QtWidgets import QDialog
from superboucle.add_scene_ui import Ui_Dialog

class AddSceneDialog(QDialog, Ui_Dialog):
    def __init__(self, gui, callback=None):
        super(AddSceneDialog, self).__init__(gui)
        self.gui = gui
        self.callback = callback
        self.setupUi(self)
        self.accepted.connect(self.onOk)
        self.show()
        self.name.setFocus()

    def onOk(self):
        self.gui.song.addScene(self.name.text())
        if self.callback:
            self.callback()