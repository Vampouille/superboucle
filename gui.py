#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Gui
"""

from PyQt5.QtWidgets import (QWidget,
                             QPushButton,
                             QApplication,
                             QSplitter,
                             QMainWindow,
                             QFileDialog)
from PyQt5.QtCore import Qt, QTimer
import clip
from ui import Ui_MainWindow


class Cell(QWidget):

    def __init__(self, clip):
        super(Cell, self).__init__()
        self.clip = clip
        self.setupUi(self)


class Gui(QMainWindow, Ui_MainWindow):

    GREEN = "QPushButton {  background-color: rgb(0,230,0);}"
    BLUE = "QPushButton {  background-color: rgb(0, 130, 240);}"
    RED = "QPushButton {  background-color: rgb(240, 0, 0);}"
    PURPLE = "QPushButton {  background-color: rgb(130, 0, 240);}"
    WHITE = "QPushButton {  background-color: rgb(255, 255, 255);}"

    STATE_COLORS = {clip.Clip.STOP: RED,
                    clip.Clip.STARTING: GREEN,
                    clip.Clip.START: GREEN,
                    clip.Clip.STOPPING: RED}
    STATE_BLINK = {clip.Clip.STOP: False,
                   clip.Clip.STARTING: True,
                   clip.Clip.START: False,
                   clip.Clip.STOPPING: True}

    BLINK_DURATION = 200

    def __init__(self, song):
        super(Gui, self).__init__()
        self.song = song
        self.setupUi(self)

        self.actionOpen.triggered.connect(self.onActionOpen)
        self.actionSave.triggered.connect(self.onActionSave)
        self.actionSave_As.triggered.connect(self.onActionSaveAs)

        self.initUI()
       
        self.setWindowTitle('Super Boucle')
        self.show()

        self.timer = QTimer()
        self.timer.state = False
        self.timer.timeout.connect(self.toogleBlinkButton)

        self.update()

    def initUI(self):

        self.groupBox.setEnabled(False)

        self.master_volume.valueChanged.connect(self.onMasterVolumeChange)
        self.master_volume.setValue(self.song.volume*256)
        self.clip_volume.valueChanged.connect(self.onClipVolumeChange)
        self.beat_diviser.valueChanged.connect(self.onBeatDiviserChange)
        self.frame_offset.valueChanged.connect(self.onFrameOffsetChange)
        self.beat_offset.valueChanged.connect(self.onBeatOffsetChange)

        self.btn_matrix = [[None for x in range(self.song.height)]
                           for x in range(self.song.width)]
        self.state_matrix = [[-1 for x in range(self.song.height)]
                             for x in range(self.song.width)]


        grid = self.gridLayout

        for x in range(self.song.width):
            for y in range(self.song.height):
                splitter = QSplitter(self)
                splitter.setOrientation(Qt.Vertical)

                # btn = Cell(self.song.clips_matrix[x][y])
                btn = QPushButton('Start/Stop', splitter)
                btn.x, btn.y = x, y
                btn.blink, btn.color = False, None
                self.btn_matrix[x][y] = btn
                btn.clicked.connect(self.onClick)
                btn.setMinimumSize(75, 50)

                edit = QPushButton('Edit', splitter)
                edit.x, edit.y = x, y
                edit.clicked.connect(self.onEdit)
                edit.setMinimumSize(75, 25)

                grid.addWidget(splitter, x, y)

        self.song.registerUI(self.update)
        self.update()


    def onClick(self):
        btn = self.sender()
        self.song.toogle(btn.x, btn.y)

    def onEdit(self):
        btn = self.sender()
        self.last_clip = self.song.clips_matrix[btn.x][btn.y]
        if clip:
            self.groupBox.setEnabled(True)
            self.groupBox.setTitle(self.last_clip.name)
            self.frame_offset.setValue(self.last_clip.frame_offset)
            self.beat_offset.setValue(self.last_clip.beat_offset)
            self.beat_diviser.setValue(self.last_clip.beat_diviser)
            self.clip_volume.setValue(self.last_clip.volume*256)
            self.clip_description.setText("Good clip !")

    def onMasterVolumeChange(self):
        self.song.volume = (self.master_volume.value() / 256)

    def onClipVolumeChange(self):
        self.last_clip.volume = (self.clip_volume.value() / 256)

    def onBeatDiviserChange(self):
        self.last_clip.beat_diviser = self.beat_diviser.value()

    def onFrameOffsetChange(self):
        self.last_clip.frame_offset = self.frame_offset.value()

    def onBeatOffsetChange(self):
        self.last_clip.beat_offset = self.beat_offset.value()

    def onActionSave(self):
        if self.song.file_name:
            self.song.save()
            print("File saved")
        else:
            self.onActionSaveAs()

    def onActionSaveAs(self):
        self.song.file_name, a = (
            QFileDialog.getSaveFileName(self,
                                        'Save As',
                                        '/home/joe/git/superboucle/',
                                        'Super Boucle Song (*.sbl)'))
        if self.song.file_name:
            self.song.save()
            print("File saved to : {}".format(self.song.file_name))

    def onActionOpen(self):
        file_name, a = (
            QFileDialog.getOpenFileName(self,
                                        'Open file',
                                        '/home/joe/git/superboucle/',
                                        'Super Boucle Song (*.sbl)'))
        if file_name:
            self.song = clip.load_song_from_file(file_name)
            self.initUI()

    def update(self):
        for clp in self.song.clips:
            # print("updating clip at {0} {1}".format(clp.x, clp.y))
            if clp.state != self.state_matrix[clp.x][clp.y]:
                self.setCellColor(clp.x,
                                  clp.y,
                                  self.STATE_COLORS[clp.state],
                                  self.STATE_BLINK[clp.state])
                self.state_matrix[clp.x][clp.y] = clp.state

    def setCellColor(self, x, y, color, blink=False):
        self.btn_matrix[x][y].setStyleSheet(color)
        self.btn_matrix[x][y].blink = blink
        self.btn_matrix[x][y].color = color
        if blink and not self.timer.isActive():
            self.timer.state = False
            self.timer.start(self.BLINK_DURATION)
        if not blink and self.timer.isActive():
            if not any([btn.blink for line in self.btn_matrix
                        for btn in line]):
                self.timer.stop()

    def toogleBlinkButton(self):
        for line in self.btn_matrix:
            for btn in line:
                if btn.blink:
                    if self.timer.state:
                        btn.setStyleSheet(btn.color)
                    else:
                        btn.setStyleSheet("")

        self.timer.state = not self.timer.state



def main():
    app = QApplication()
    clip = Clip('beep-stereo.wav', beat_diviser=4, frame_offset=0, beat_offset=1)  # 1500
    song = Song(8, 8)
    song.add_clip(clip, 1, 2)

    app = QApplication()
    Gui(song)
    app.exec_()
   


if __name__ == '__main__':
    main()
