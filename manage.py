from PyQt5.QtWidgets import QDialog, QFileDialog
from manage_ui import Ui_Dialog
import json


class ManageDialog(QDialog, Ui_Dialog):

    def __init__(self, parent):
        super(ManageDialog, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        for device in self.gui.devices[1:]:
            self.list.addItem(device.name)
        self.deleteButton.clicked.connect(self.onDelete)
        self.importButton.clicked.connect(self.onImport)
        self.exportButton.clicked.connect(self.onExport)
        self.show()

    def onDelete(self):
        if self.list.currentRow() != -1:
            device = self.gui.devices[self.list.currentRow() + 1]
            self.gui.devices.remove(device)
            self.gui.devicesComboBox.removeItem(self.list.currentRow() + 1)
            self.list.takeItem(self.list.currentRow())

    def onImport(self):
        file_name, a = (
            QFileDialog.getOpenFileName(self,
                                        'Open file',
                                        '/home/joe/git/superboucle/',
                                        'Super Boucle Mapping (*.sbm)'))
        with open(file_name, 'r') as f:
            read_data = f.read()
        mapping = json.loads(read_data)
        self.list.addItem(mapping['name'])
        self.gui.addDevice(mapping)

    def onExport(self):
        device = self.gui.devices[self.list.currentRow() + 1]
        file_name, a = (
            QFileDialog.getSaveFileName(self,
                                        'Save As',
                                        '/home/joe/git/superboucle/',
                                        'Super Boucle Mapping (*.sbm)'))

        with open(file_name, 'w') as f:
            f.write(json.dumps(device.mapping))
