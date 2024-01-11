from PyQt5.QtWidgets import QDialog, QListWidgetItem, QTableWidget, QTableWidgetItem, QInputDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSize
from superboucle.port import AudioPort, MidiPort
from superboucle.port_manager_ui import Ui_Dialog
from superboucle.edit_port_regexp_ui import Ui_Dialog as Ui_Dialog_Regexp
from superboucle.jack_client import client

from superboucle.song import verify_ext


class PortManager(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(PortManager, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        #self.loadPortlistBtn.clicked.connect(self.onLoadPortlist)

        self.audioPorts.setColumnCount(3)
        self.audioPorts.setHorizontalHeaderLabels(['Name', 'Auto Connect Regexp', 'Status'])
        self.audioPorts.itemClicked.connect(self.onEditAudioRegexp)

        self.midiPorts.setColumnCount(3)
        self.midiPorts.setHorizontalHeaderLabels(['Name', 'Auto Connect Regexp', 'Status'])
        self.midiPorts.itemClicked.connect(self.onEditMidiRegexp)

        self.addAudioPort.clicked.connect(self.onAddAudioPort)
        self.addMidiPort.clicked.connect(self.onAddMidiPort)
        self.removeAudioPort.clicked.connect(self.onRemoveAudioPort)
        self.removeMidiPort.clicked.connect(self.onRemoveMidiPort)

        self.editAudioRecord.clicked.connect(self.onEditAudioRecord)
        self.editMidiClock.clicked.connect(self.onEditMidiClock)
        self.editMidiControl.clicked.connect(self.onEditMidiControl)

        self.update()

        self.show()

    def update(self):
        # Audio
        self.audioPorts.clearContents()
        self.audioPorts.setRowCount(len(self.gui.song.outputsPorts))
        row = 0
        for p in self.gui.song.outputsPorts:
            item = QTableWidgetItem(p.name)
            self.audioPorts.setItem(row, 0, item)
            item = QTableWidgetItem("" if p.regexp is None else p.regexp)
            item.setSizeHint(QSize(150, 20))
            item.port = p
            self.audioPorts.setItem(row, 1, item)
            row += 1
        self.audioPorts.resizeColumnsToContents()
        self.audioPorts.sortItems(0)

        # Midi
        self.midiPorts.clearContents()
        self.midiPorts.setRowCount(len(self.gui.song.outputsMidiPorts))
        row = 0
        for p in self.gui.song.outputsMidiPorts:
            item = QTableWidgetItem(p.name)
            item.port = p
            self.midiPorts.setItem(row, 0, item)
            item = QTableWidgetItem("" if p.regexp is None else p.regexp)
            item.setSizeHint(QSize(150, 20))
            item.port = p
            self.midiPorts.setItem(row, 1, item)
            row += 1
        self.midiPorts.resizeColumnsToContents()
        self.midiPorts.sortItems(0)

    def onEditAudioRegexp(self, item):
        if item.column() == 1:
            self._onEditRegexp(item, "audio", f'{item.port.name} Edit Auto Connect Regexp')
        else:
            self.audioPorts.item(item.row(), 0).setSelected(True)
            self.audioPorts.item(item.row(), 1).setSelected(True)

    def onEditMidiRegexp(self, item):
        if item.column() == 1:
            self._onEditRegexp(item, "midi", f'{item.port.name} Edit Auto Connect Regexp')
        else:
            self.midiPorts.item(item.row(), 0).setSelected(True)
            self.midiPorts.item(item.row(), 1).setSelected(True)

    def _onEditRegexp(self, item, type, title):
            EditPortRegexpDialog(self, type, item, title)

    def onAddAudioPort(self):
        text, ok_pressed = QInputDialog.getText(self, 'Add New Audio Port', 'Name:')

        if ok_pressed:
            self.gui.song.outputsPorts.add(AudioPort(name=text))
            self.update()

    def onAddMidiPort(self):
        text, ok_pressed = QInputDialog.getText(self, 'Add New Midi Port', 'Name:')

        if ok_pressed:
            self.gui.song.outputsMidiPorts.add(MidiPort(name=text))
            self.update()

    def onRemoveAudioPort(self):
        selected_item = self.audioPorts.currentItem()

        if selected_item:
            port = self.audioPorts.item(selected_item.row(), 1).port
            self.gui.song.removeAudioPort(port)
            self.update()

    def onRemoveMidiPort(self):
        selected_item = self.midiPorts.currentItem()

        if selected_item:
            port = self.midiPorts.item(selected_item.row(), 1).port
            self.gui.song.removeMidiPort(port)
            self.update()

    def onEditAudioRecord(self):
        pass

    def onEditMidiClock(self):
        pass

    def onEditMidiControl(self):
        pass

    #def onLoadPortlist(self):
    #    file_name, a = (
    #        self.gui.getOpenFileName('Open Portlist',
    #                                 'Super Boucle Portlist (*.sbl)',
    #                                 self))
    #    if not file_name:
    #        return
    #    with open(file_name, 'r') as f:
    #        read_data = f.read()
    #    data = json.loads(read_data)
    #    self.gui.song._outputs = data["outputs"]
    #    for tp in zip(self.gui.song.clips_matrix, data["clips"]):
    #        for (clip, out) in zip(*tp):
    #            if isinstance(clip, Clip):
    #                clip.output = out
    #    self.gui.updatePorts.emit()

    #def onSavePortlist(self):
    #    file_name, a = (
    #        self.gui.getSaveFileName('Save Portlist',
    #                                 'Super Boucle Portlist (*.sbl)',
    #                                 self))

    #    if file_name:
    #        file_name = verify_ext(file_name, 'sbl')
    #        with open(file_name, 'w') as f:
    #            data = {"clips": [
    #                [c.output if isinstance(c, Clip) else Clip.DEFAULT_OUTPUT
    #                 for c in cliprow] for cliprow in
    #                self.gui.song.clips_matrix],
    #                    "outputs": self.gui.song.outputs}
    #            f.write(json.dumps(data))

class EditPortRegexpDialog(QDialog, Ui_Dialog_Regexp):
    def __init__(self, parent, type, item, title):
        super(EditPortRegexpDialog, self).__init__(parent)
        self.type = type
        self.item: QTableWidgetItem = item 
        self.setupUi(self)
        self.setWindowTitle(title)

        # Display Ports
        for port in self.getPorts(""):
            self.ports.addItem(QListWidgetItem(port.name))

        # Connect
        self.buttonBox.accepted.connect(self.save)
        self.regexp.setText(self.item.text())
        self.regexp.textChanged.connect(self.updatePorts)
        self.updatePorts()
        self.show()

    def getPorts(self, regexp):
        return client.get_ports(regexp,
                                is_input=True,
                                is_physical=True,
                                is_midi=self.type == 'midi',
                                is_audio=self.type == 'audio')

    def updatePorts(self):

        regexp = self.regexp.text()
        if len(regexp):
            match_ports = [p.name for p in self.getPorts(self.regexp.text())]
        else:
            match_ports = []
        for i in range(self.ports.count()):
            item = self.ports.item(i)
            if item.text() in match_ports:
                #item.setBackground(QColor(9, 212, 219))
                item.setBackground(QColor(6, 147, 152))
            else:
                item.setData(Qt.BackgroundRole, None)

    def save(self):
        self.item.setText(self.regexp.text())
        self.item.port.regexp = self.regexp.text()
        self.item.tableWidget().resizeColumnsToContents()
        self.accept()