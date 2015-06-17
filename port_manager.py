from PyQt5.QtWidgets import QDialog, QLineEdit, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
from port_manager_ui import Ui_Dialog
from clip import verify_ext, Clip
import json


class PortManager(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(PortManager, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.updateList()
        self.removePortBtn.clicked.connect(self.onRemove)
        self.addPortBtn.clicked.connect(self.onAddPort)
        self.loadPortlistBtn.clicked.connect(self.onLoadPortlist)
        self.savePortlistBtn.clicked.connect(self.onSavePortlist)
        # self.portList.setDragDropMode(QAbstractItemView.InternalMove)
        # self.portList.model().rowsMoved.connect(self.onMoveRows)
        self.autoconnectCBox.setChecked(self.gui.auto_connect)
        # self.autoconnectCBox.stateChanged.connect(self.onCheckAutoconnect)
        self.finished.connect(self.onFinished)
        self.show()

    def updateList(self):
        self.portList.clear()
        for name in self.gui.song.outputs:
            this_item = QListWidgetItem(name)
            this_item.setFlags(this_item.flags() | Qt.ItemIsEditable)
            self.portList.addItem(this_item)
        self.gui.updatePorts()

    def onAddPort(self):
        msg = "As of now you can only add Ports directly in the " \
              "output field when editing clips."
        QMessageBox.question(self, 'Not implemented.', msg, QMessageBox.Ok)
        return
        # text, ok = QInputDialog.getText(self, "Add a port..", "port name ",
        #                                 QLineEdit.Normal,
        #                                 "Out_{}".format(
        #                                     len(self.gui.song.outputs)))
        # if not ok:
        #     return
        # self.gui.song.outputs.append(text)
        # self.updateList()

    def onRemove(self):
        id = self.portList.currentRow()
        if id != -1:
            currentOutput = self.gui.song.outputs[id]
            for c in self.gui.song.clips_by_output(currentOutput):
                c.output = Clip.DEFAULT_OUTPUT
            self.updateList()

    def onLoadPortlist(self):
        file_name, a = self.gui.getOpenFileName('Open Portlist',
                                                'Super Boucle Portlist (*.sbl)',
                                                self)
        if not file_name:
            return
        with open(file_name, 'r') as f:
            read_data = f.read()
        portmatrix = json.loads(read_data)
        for tp in zip(self.gui.song.clips_matrix, portmatrix):
            for (clip, out) in zip(*tp):
                if isinstance(clip, Clip):
                    clip.output = out
        self.updateList()

    def onSavePortlist(self):
        file_name, a = self.gui.getSaveFileName('Save Portlist',
                                                'Super Boucle Portlist (*.sbl)',
                                                self)

        if file_name:
            file_name = verify_ext(file_name, 'sbl')
            with open(file_name, 'w') as f:
                data = [
                    [c.output if isinstance(c, Clip) else Clip.DEFAULT_OUTPUT
                     for c in cliprow] for cliprow in
                    self.gui.song.clips_matrix]
                f.write(json.dumps(data))

    def onFinished(self):
        pass
        # self.gui.updateDevices()
