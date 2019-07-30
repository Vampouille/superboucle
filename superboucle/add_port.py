from PyQt5.QtWidgets import QDialog
from add_port_ui import Ui_Dialog


class AddPortDialog(QDialog, Ui_Dialog):
    def __init__(self, gui, callback=None):
        super(AddPortDialog, self).__init__(gui)
        self.gui = gui
        self.callback = callback
        self.setupUi(self)
        self.accepted.connect(self.onOk)
        self.rejected.connect(self.onCancel)
        self.show()
        self.name.setFocus()

    def onOk(self):
        self.gui.addPort(self.name.text())
        if self.callback:
            self.callback()

    def onCancel(self):
        if self.gui.last_clip:
            self.gui.output.setCurrentText(self.gui.last_clip.output)
