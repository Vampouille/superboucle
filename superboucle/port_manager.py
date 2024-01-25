from PyQt5.QtWidgets import (
    QDialog,
    QListWidgetItem,
    QAbstractItemView,
    QTableWidgetItem,
    QInputDialog,
)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt, QSize, QRect
from superboucle.port import AudioPort, MidiPort
from superboucle.port_manager_ui import Ui_Dialog
from superboucle.edit_port_regexp_ui import Ui_Dialog as Ui_Dialog_Regexp

from superboucle.song import verify_ext

TOOLTIP_STYLE = """
    QToolTip {
        background-color: rgb(6, 147, 152);
        padding: 5px;
    }
"""
class PortManager(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(PortManager, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.setWindowTitle("Port Manager")

        # self.loadPortlistBtn.clicked.connect(self.onLoadPortlist)

        self.audioPorts.setColumnCount(3)
        self.audioPorts.setHorizontalHeaderLabels(
            ["Name", "Auto Connect Regexp", "Status"]
        )
        self.audioPorts.setStyleSheet(TOOLTIP_STYLE)
        self.audioPorts.itemClicked.connect(self.onEditAudioRegexp)

        self.midiPorts.setColumnCount(3)
        self.midiPorts.setHorizontalHeaderLabels(
            ["Name", "Auto Connect Regexp", "Status"]
        )
        self.midiPorts.setStyleSheet(TOOLTIP_STYLE)
        self.midiPorts.itemClicked.connect(self.onEditMidiRegexp)

        self.addAudioPort.clicked.connect(self.onAddAudioPort)
        self.addMidiPort.clicked.connect(self.onAddMidiPort)
        self.removeAudioPort.clicked.connect(self.onRemoveAudioPort)
        self.removeMidiPort.clicked.connect(self.onRemoveMidiPort)

        self.editAudioRecord.clicked.connect(self.onEditAudioRecord)
        self.editMidiRecord.clicked.connect(self.onEditMidiRecord)
        self.editMidiClock.clicked.connect(self.onEditMidiClock)
        self.editMidiControlInput.clicked.connect(self.onEditMidiControlInput)
        self.editMidiControlOutput.clicked.connect(self.onEditMidiControlOutput)

        self.audioRecord.textChanged.connect(self.onChangedAudioRecord)
        self.midiRecord.textChanged.connect(self.onChangedMidiRecord)
        self.midiClock.textChanged.connect(self.onChangedMidiClock)
        self.midiControlInput.textChanged.connect(self.onChangedMidiControlInput)
        self.midiControlOutput.textChanged.connect(self.onChangedMidiControlOutput)

        self.gui.superboucleConnectionChangeSignal.connect(self.updateStatus)
        self.connected = QBrush(QColor(6, 147, 152))
        self.not_connected = Qt.NoBrush

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

        # Default Port
        self.audioRecord.setText(self.gui.song.audioRecordRegexp)
        self.midiClock.setText(self.gui.song.midiClockRegexp)
        self.midiControlInput.setText(self.gui.song.midiControlInputRegexp)
        self.midiControlOutput.setText(self.gui.song.midiControlOutputRegexp)

        self.updateStatus()

    def updateStatus(self):
        for p in self.gui.song.outputsPorts:
            # Search for port row
            for row in range(self.audioPorts.rowCount()):
                if self.audioPorts.item(row, 0).text() == p.name:
                    self.audioPorts.setItem(row, 2, self.generateConnectionsStatus(p))
        self.audioPorts.resizeColumnsToContents()

        # MIDI
        for p in self.gui.song.outputsMidiPorts:
            for row in range(self.midiPorts.rowCount()):
                if self.midiPorts.item(row, 0).text() == p.name:
                    self.midiPorts.setItem(row, 2, self.generateConnectionsStatus(p))
        self.midiPorts.resizeColumnsToContents()

        # Default Ports
        self.updateConnectionWidget(self.audioRecordConnections, [self.gui.inL, self.gui.inR])
        self.updateConnectionWidget(self.midiRecordConnections, [self.gui.note_midi_in])
        self.updateConnectionWidget(self.midiClockConnections, [self.gui.sync_midi_in])
        self.updateConnectionWidget(self.midiControlInputConnections, [self.gui.cmd_midi_in])
        self.updateConnectionWidget(self.midiControlOutputConnections, [self.gui.cmd_midi_out])

    def updateConnectionWidget(self, widget, ports):
        res = []
        for p in ports:
            for other_port in p.connections:
                res.append(other_port.name)
        widget.setText("%s connection(s)" % len(res))
        widget.setToolTip("\n".join(res))
        if len(res):
            widget.setStyleSheet("background-color: rgb(6, 147, 152); padding: 5px;")
        else:
            widget.setStyleSheet("padding: 5px;")

    def generateConnectionsStatus(self, port):
        desc = self.generateStatus(port)
        item = QTableWidgetItem("%s connection(s)" % len(desc))
        item.setToolTip("\n".join(desc))
        if len(desc):
            item.setBackground(self.connected)
        return item

    def generateStatus(self, port):
        if isinstance(port, AudioPort):
            jack_ports = [
                p
                for p in self.gui._jack_client.outports
                if p.shortname in port.getShortNames()
            ]
        else:
            jack_ports = [
                p
                for p in self.gui._jack_client.midi_outports
                if p.shortname in port.getShortNames()
            ]

        res = []
        for jack_port in jack_ports:
            for other_port in jack_port.connections:
                res.append(other_port.name)
        return res

    def onEditAudioRegexp(self, item):
        if item.column() == 1:
            regexp = self._onEditRegexp(
                item, "audio", "input", f"{item.port.name} Edit Auto Connect Regexp"
            )
            if regexp is not None:
                item.port.regexp = regexp
                self.gui.autoConnectPorts()
        else:
            self.audioPorts.item(item.row(), 0).setSelected(True)
            self.audioPorts.item(item.row(), 1).setSelected(True)

    def onEditMidiRegexp(self, item):
        if item.column() == 1:
            regexp = self._onEditRegexp(
                item, "midi", "input", f"{item.port.name} Edit Auto Connect Regexp"
            )
            if regexp is not None:
                item.port.regexp = regexp
                self.gui.autoConnectPorts()
        else:
            self.midiPorts.item(item.row(), 0).setSelected(True)
            self.midiPorts.item(item.row(), 1).setSelected(True)

    def _onEditRegexp(self, item, type, way, title):
        dialog = EditPortRegexpDialog(self, type, way, item, title)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            item.setText(dialog.regexp.text())
            return dialog.regexp.text()
        else:
            return None

    def onAddAudioPort(self):
        text, ok_pressed = QInputDialog.getText(self, "Add New Audio Port", "Name:")

        if ok_pressed:
            self.gui.addAudioPort(text)
            self.update()

    def onAddMidiPort(self):
        text, ok_pressed = QInputDialog.getText(self, "Add New Midi Port", "Name:")

        if ok_pressed:
            self.gui.addMidiPort(text)
            self.update()

    def onRemoveAudioPort(self):
        selected_item = self.audioPorts.currentItem()

        if selected_item:
            port = self.audioPorts.item(selected_item.row(), 1).port
            self.gui.removeAudioPort(port)
            self.update()

    def onRemoveMidiPort(self):
        selected_item = self.midiPorts.currentItem()

        if selected_item:
            port = self.midiPorts.item(selected_item.row(), 1).port
            self.gui.removeMidiPort(port)
            self.update()

    def onEditAudioRecord(self):
        regexp = self._onEditRegexp(
            self.audioRecord,
            "audio",
            "output",
            "Audio Record Input Edit Auto Connect Regexp",
        )
        if regexp is not None:
            self.gui.song.audioRecordRegexp = regexp
            self.gui.autoConnectPorts()

    def onEditMidiRecord(self):
        regexp = self._onEditRegexp(
            self.midiRecord,
            "midi",
            "output",
            "Midi Record Input Edit Auto Connect Regexp",
        )
        if regexp is not None:
            self.gui.song.midiRecordRegexp = regexp
            self.gui.autoConnectPorts()

    def onEditMidiClock(self):
        regexp = self._onEditRegexp(
            self.midiClock,
            "midi",
            "output",
            "Midi Clock Input Edit Auto Connect Regexp",
        )
        if regexp is not None:
            self.gui.song.midiClockRegexp = regexp
            self.gui.autoConnectPorts()

    def onEditMidiControlInput(self):
        regexp = self._onEditRegexp(
            self.midiControlInput,
            "midi",
            "output",
            "Midi Control Input Edit Auto Connect Regexp",
        )
        if regexp is not None:
            self.gui.song.midiControlInputRegexp = regexp
            self.gui.autoConnectPorts()

    def onEditMidiControlOutput(self):
        regexp = self._onEditRegexp(
            self.midiControlOutput,
            "midi",
            "input",
            "Midi Control Output Edit Auto Connect Regexp",
        )
        if regexp is not None:
            self.gui.song.midiControlOutputRegexp = regexp
            self.gui.autoConnectPorts()

    def onChangedAudioRecord(self):
        self.gui.song.audioRecordRegexp = self.audioRecord.text()
        self.gui.autoConnectPorts()

    def onChangedMidiRecord(self):
        self.gui.song.midiRecordRegexp = self.midiRecord.text()
        self.gui.autoConnectPorts()

    def onChangedMidiClock(self):
        self.gui.song.midiClockRegexp = self.midiClock.text()
        self.gui.autoConnectPorts()

    def onChangedMidiControlInput(self):
        self.gui.song.midiControlInputRegexp = self.midiControlInput.text()
        self.gui.autoConnectPorts()

    def onChangedMidiControlOutput(self):
        self.gui.song.midiControlOutputRegexp = self.midiControlOutput.text()
        self.gui.autoConnectPorts()

    # def onLoadPortlist(self):
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

    # def onSavePortlist(self):
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
    def __init__(self, parent, type, way, item, title):
        super(EditPortRegexpDialog, self).__init__(parent)
        self.client = parent.gui._jack_client
        self.type = type
        self.way = way
        self.item: QTableWidgetItem = item
        self.setupUi(self)
        self.setWindowTitle(title)

        # Display Ports
        self.ports.setSelectionMode(QAbstractItemView.NoSelection)
        self.ports.clearFocus()

        # Connect
        self.regexp.setText(self.item.text())
        self.regexp.textChanged.connect(self.updatePortSelection)
        parent.gui.jackConnectionChangeSignal.connect(self.updatePorts)
        self.updatePorts()

    def getPorts(self, regexp):
        return [
            p
            for p in self.client.get_ports(
                regexp,
                is_input=True if self.way == "input" else False,
                is_output=True if self.way == "output" else False,
                is_midi=self.type == "midi",
                is_audio=self.type == "audio",
            )
            if not self.client.owns(p)
        ]

    def updatePorts(self):
        self.ports.clear()
        for port in self.getPorts(""):
            self.ports.addItem(QListWidgetItem(port.name))
        self.updatePortSelection()

    def updatePortSelection(self):
        regexp = self.regexp.text()
        if len(regexp):
            match_ports = [p.name for p in self.getPorts(self.regexp.text())]
        else:
            match_ports = []
        for i in range(self.ports.count()):
            item = self.ports.item(i)
            if item.text() in match_ports:
                # item.setBackground(QColor(9, 212, 219))
                item.setBackground(QColor(6, 147, 152))
            else:
                item.setData(Qt.BackgroundRole, None)
