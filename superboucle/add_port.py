from PyQt5.QtWidgets import QDialog
from superboucle.add_port_ui import Ui_Dialog


class AddPortDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, okCallback, cancelCallback):
        super(AddPortDialog, self).__init__(parent)
        self.okCallback = okCallback
        self.cancelCallback = cancelCallback
        self.setupUi(self)
        self.accepted.connect(self.onOk)
        self.rejected.connect(self.onCancel)
        self.show()
        self.name.setFocus()

    def onOk(self):
        self.okCallback(self.name.text())

    def onCancel(self):
        self.cancelCallback()
