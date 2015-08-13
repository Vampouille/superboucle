from PyQt5.QtWidgets import QDialog
from manage_ui import Ui_Dialog
from learn import LearnDialog
from device import Device
from clip import verify_ext
import json


class ManageDialog(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(ManageDialog, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        for device in self.gui.devices[1:]:
            self.list.addItem(device.name)
        self.editButton.clicked.connect(self.onEdit)
        self.deleteButton.clicked.connect(self.onDelete)
        self.importButton.clicked.connect(self.onImport)
        self.exportButton.clicked.connect(self.onExport)
        self.finished.connect(self.onFinished)
        self.show()

    def onEdit(self):
        if self.list.currentRow() != -1:
            device = self.gui.devices[self.list.currentRow() + 1]
            self.gui.learn_device = LearnDialog(self.gui,
                                                self.updateDevice,
                                                device)
            self.gui.is_learn_device_mode = True

    def onDelete(self):
        if self.list.currentRow() != -1:
            device = self.gui.devices[self.list.currentRow() + 1]
            self.gui.devices.remove(device)
            self.list.takeItem(self.list.currentRow())

    def onImport(self):
        file_name, a = self.gui.getOpenFileName('Open Device',
                                                'Super Boucle Device (*.sbd)',
                                                self)
        with open(file_name, 'r') as f:
            read_data = f.read()
        device = Device.fromJson(read_data)
        self.list.addItem(device.name)
        self.gui.devices.append(device)

    def onExport(self):
        device = self.gui.devices[self.list.currentRow() + 1]
        file_name, a = self.gui.getSaveFileName('Save Device',
                                                'Super Boucle Device (*.sbd)',
                                                self)
        if file_name:
            file_name = verify_ext(file_name, 'sbd')
            with open(file_name, 'w') as f:
                f.write(device.toJson())

    def onFinished(self):
        self.gui.updateDevices()

    def updateDevice(self, device):
        self.list.clear()
        for device in self.gui.devices[1:]:
            self.list.addItem(device.name)
        self.gui.is_learn_device_mode = False
        self.gui.redraw()
