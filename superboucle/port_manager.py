from PyQt5.QtWidgets import QDialog, QListWidgetItem
from port_manager_ui import Ui_Dialog
from add_port import AddPortDialog
from clip import verify_ext, Clip
import json


class PortManager(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(PortManager, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.backup_indixes = []
        self.updateList()
        self.removePortBtn.clicked.connect(self.onRemove)
        self.addPortBtn.clicked.connect(self.onAddPort)
        self.loadPortlistBtn.clicked.connect(self.onLoadPortlist)
        self.savePortlistBtn.clicked.connect(self.onSavePortlist)
        self.autoconnectCBox.setChecked(self.gui.auto_connect)
        self.autoconnectCBox.stateChanged.connect(self.onCheckAutoconnect)
        self.finished.connect(self.onFinished)
        self.gui.updatePorts.connect(self.updateList)
        self.show()

    def updateList(self):
        self.portList.clear()
        self.backup_indixes = list(self.gui.song.outputsPorts)
        for name in self.backup_indixes:
            this_item = QListWidgetItem(name)
            this_item.setFlags(this_item.flags())
            self.portList.addItem(this_item)

    def onAddPort(self):
        AddPortDialog(self.gui, callback=self.updateList)

    def onRemove(self):
        currentItem = self.portList.currentItem()
        if currentItem:
            port_name = currentItem.text()
            self.gui.removePort(port_name)
            self.updateList()

    def onLoadPortlist(self):
        file_name, a = (
            self.gui.getOpenFileName('Open Portlist',
                                     'Super Boucle Portlist (*.sbl)',
                                     self))
        if not file_name:
            return
        with open(file_name, 'r') as f:
            read_data = f.read()
        data = json.loads(read_data)
        self.gui.song._outputs = data["outputs"]
        for tp in zip(self.gui.song.clips_matrix, data["clips"]):
            for (clip, out) in zip(*tp):
                if isinstance(clip, Clip):
                    clip.output = out
        self.gui.updatePorts.emit()

    def onSavePortlist(self):
        file_name, a = (
            self.gui.getSaveFileName('Save Portlist',
                                     'Super Boucle Portlist (*.sbl)',
                                     self))

        if file_name:
            file_name = verify_ext(file_name, 'sbl')
            with open(file_name, 'w') as f:
                data = {"clips": [
                    [c.output if isinstance(c, Clip) else Clip.DEFAULT_OUTPUT
                     for c in cliprow] for cliprow in
                    self.gui.song.clips_matrix],
                        "outputs": self.gui.song.outputs}
                f.write(json.dumps(data))

    def onCheckAutoconnect(self):
        self.gui.auto_connect = self.autoconnectCBox.isChecked()

    def onFinished(self):
        pass
        # self.gui.updateDevices()
