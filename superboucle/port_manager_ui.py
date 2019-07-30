# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'port_manager_ui.ui'
#
# Created: Mon Mar 14 12:27:24 2016
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(320, 295)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.portList = QtWidgets.QListWidget(Dialog)
        self.portList.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.portList.setSizeIncrement(QtCore.QSize(100, 100))
        self.portList.setMovement(QtWidgets.QListView.Static)
        self.portList.setResizeMode(QtWidgets.QListView.Adjust)
        self.portList.setObjectName("portList")
        self.horizontalLayout.addWidget(self.portList)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.addPortBtn = QtWidgets.QPushButton(Dialog)
        self.addPortBtn.setObjectName("addPortBtn")
        self.verticalLayout_3.addWidget(self.addPortBtn)
        self.removePortBtn = QtWidgets.QPushButton(Dialog)
        self.removePortBtn.setObjectName("removePortBtn")
        self.verticalLayout_3.addWidget(self.removePortBtn)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.loadPortlistBtn = QtWidgets.QPushButton(Dialog)
        self.loadPortlistBtn.setObjectName("loadPortlistBtn")
        self.verticalLayout_3.addWidget(self.loadPortlistBtn)
        self.savePortlistBtn = QtWidgets.QPushButton(Dialog)
        self.savePortlistBtn.setObjectName("savePortlistBtn")
        self.verticalLayout_3.addWidget(self.savePortlistBtn)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.autoconnectCBox = QtWidgets.QCheckBox(Dialog)
        self.autoconnectCBox.setObjectName("autoconnectCBox")
        self.gridLayout.addWidget(self.autoconnectCBox, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Port Manager"))
        self.addPortBtn.setText(_translate("Dialog", "Add Port"))
        self.removePortBtn.setText(_translate("Dialog", "Remove Port"))
        self.loadPortlistBtn.setText(_translate("Dialog", "Load Portlist"))
        self.savePortlistBtn.setText(_translate("Dialog", "Save Portlist"))
        self.autoconnectCBox.setText(_translate("Dialog", "autoconnect main ports on program start"))

