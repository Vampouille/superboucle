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
from PyQt5.QtWidgets import (QGridLayout,
                             QWidget,
                             QPushButton,
                             QApplication)

import clip


class Gui(QWidget):

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
        self.btn_matrix = [[None for x in range(self.song.height)]
                           for x in range(self.song.width)]
        self.state_matrix = [[-1 for x in range(self.song.height)]
                             for x in range(self.song.width)]

        grid = QGridLayout(self)
        self.setLayout(grid)

        for x in range(self.song.width):
            for y in range(self.song.height):
                btn = QPushButton('Dialog', self)
                btn.x, btn.y = x, y
                self.btn_matrix[x][y] = btn
                btn.clicked.connect(self.onClick)
                btn.setMinimumSize(75, 75)
                grid.addWidget(btn, x, y)

        self.setGeometry(300, 300, 250, 180)
        self.setWindowTitle('Color dialog')
        self.show()
    
    def onClick(self):
        btn = self.sender()
        self.song.toogle(btn.x, btn.y)
        
        print("Event {0} {1} {2}".format(btn.x, btn.y, btn))

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
