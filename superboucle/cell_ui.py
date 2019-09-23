# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'superboucle/cell_ui.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Cell(object):
    def setupUi(self, Cell):
        Cell.setObjectName("Cell")
        Cell.resize(255, 225)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(Cell.sizePolicy().hasHeightForWidth())
        Cell.setSizePolicy(sizePolicy)
        Cell.setMinimumSize(QtCore.QSize(120, 120))
        font = QtGui.QFont()
        font.setFamily("Lato")
        Cell.setFont(font)
        self.cell_frame = QtWidgets.QFrame(Cell)
        self.cell_frame.setGeometry(QtCore.QRect(0, 0, 110, 110))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cell_frame.sizePolicy().hasHeightForWidth())
        self.cell_frame.setSizePolicy(sizePolicy)
        self.cell_frame.setStyleSheet("#frame {border: 0px;\n"
"    background-color: rgb(217, 217, 217);\n"
"border-radius: 10px;}")
        self.cell_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.cell_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.cell_frame.setObjectName("cell_frame")
        self.clip_name = QtWidgets.QLabel(self.cell_frame)
        self.clip_name.setGeometry(QtCore.QRect(5, 6, 102, 20))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.clip_name.setFont(font)
        self.clip_name.setText("")
        self.clip_name.setAlignment(QtCore.Qt.AlignCenter)
        self.clip_name.setObjectName("clip_name")
        self.clip_position = QtWidgets.QProgressBar(self.cell_frame)
        self.clip_position.setGeometry(QtCore.QRect(7, 89, 97, 16))
        self.clip_position.setMaximum(97)
        self.clip_position.setProperty("value", 0)
        self.clip_position.setTextVisible(False)
        self.clip_position.setObjectName("clip_position")
        self.edit = QtWidgets.QPushButton(self.cell_frame)
        self.edit.setGeometry(QtCore.QRect(20, 60, 71, 23))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(True)
        font.setWeight(50)
        self.edit.setFont(font)
        self.edit.setObjectName("edit")
        self.start_stop = QtWidgets.QPushButton(self.cell_frame)
        self.start_stop.setGeometry(QtCore.QRect(20, 30, 71, 23))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(True)
        font.setWeight(50)
        self.start_stop.setFont(font)
        self.start_stop.setObjectName("start_stop")

        self.retranslateUi(Cell)
        QtCore.QMetaObject.connectSlotsByName(Cell)

    def retranslateUi(self, Cell):
        _translate = QtCore.QCoreApplication.translate
        Cell.setWindowTitle(_translate("Cell", "Form"))
        self.edit.setText(_translate("Cell", "Edit"))
        self.start_stop.setText(_translate("Cell", "Start/Stop"))

