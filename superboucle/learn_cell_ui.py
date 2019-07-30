# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'learn_cell_ui.ui'
#
# Created: Mon Mar 14 12:27:23 2016
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LearnCell(object):
    def setupUi(self, LearnCell):
        LearnCell.setObjectName("LearnCell")
        LearnCell.resize(94, 40)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(LearnCell.sizePolicy().hasHeightForWidth())
        LearnCell.setSizePolicy(sizePolicy)
        LearnCell.setMinimumSize(QtCore.QSize(40, 40))
        font = QtGui.QFont()
        font.setFamily("Lato")
        LearnCell.setFont(font)
        self.cell_frame = QtWidgets.QFrame(LearnCell)
        self.cell_frame.setGeometry(QtCore.QRect(0, 0, 40, 40))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cell_frame.sizePolicy().hasHeightForWidth())
        self.cell_frame.setSizePolicy(sizePolicy)
        self.cell_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.cell_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.cell_frame.setObjectName("cell_frame")
        self.label = QtWidgets.QLabel(self.cell_frame)
        self.label.setGeometry(QtCore.QRect(3, 2, 35, 39))
        self.label.setText("")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")

        self.retranslateUi(LearnCell)
        QtCore.QMetaObject.connectSlotsByName(LearnCell)

    def retranslateUi(self, LearnCell):
        _translate = QtCore.QCoreApplication.translate
        LearnCell.setWindowTitle(_translate("LearnCell", "Form"))

