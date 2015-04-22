#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode PyQt4 tutorial 

In this example, we select a colour value
from the QtGui.QColorDialog and change the background
colour of a QtGui.QFrame widget. 

author: Jan Bodnar
website: zetcode.com
last edited: October 2011
"""
# self.btn.setStyleSheet("QPushButton {  background-color: green;}")


import sys
from PyQt5.QtWidgets import (QWidget,
                             QPushButton,
                             QApplication,
                             QSplitter,
                             QLabel,
                             QMainWindow)
from PyQt5.QtCore import Qt
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
    
    STATE_COLORS = {clip.Clip.STOP: RED,
                    clip.Clip.STARTING: BLUE,
                    clip.Clip.START: GREEN,
                    clip.Clip.STOPPING: PURPLE}

    def __init__(self, song):
        super(Gui, self).__init__()
        self.song = song
        self.initUI()
        song.registerUI(self.update)

    def initUI(self):
        self.setupUi(self)
        self.groupBox.setEnabled(False)
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
                self.btn_matrix[x][y] = btn
                btn.clicked.connect(self.onClick)
                btn.setMinimumSize(75, 50)

                edit = QPushButton('Edit', splitter)
                edit.x, edit.y = x, y
                edit.clicked.connect(self.onEdit)
                edit.setMinimumSize(75, 25)

                grid.addWidget(splitter, x, y)

        self.setGeometry(800, 400, 250, 180)
        self.setWindowTitle('Color dialog')
        self.show()
    
    def onClick(self):
        btn = self.sender()
        self.song.toogle(btn.x, btn.y)
        
        print("Event {0} {1} {2}".format(btn.x, btn.y, btn))

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
            
    def onClipVolumeChange(self):
        self.last_clip.volume = (self.clip_volume.value() / 256)

    def onBeatDiviserChange(self):
        self.last_clip.beat_diviser = self.beat_diviser.value()

    def onFrameOffsetChange(self):
        self.last_clip.frame_offset = self.frame_offset.value()

    def onBeatOffsetChange(self):
        self.last_clip.beat_offset = self.beat_offset.value()

    def update(self):
        for clp in self.song.clips:
            print("updating clip at {0} {1}".format(clp.x, clp.y))
            if clp.state != self.state_matrix[clp.x][clp.y]:
                self.setCellColor(clp.x,
                                  clp.y,
                                  self.STATE_COLORS[clp.state])
                self.state_matrix[clp.x][clp.y] = clp.state

        print('update')
    
    def setCellColor(self, x, y, color):
        self.btn_matrix[x][y].setStyleSheet(color)

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
