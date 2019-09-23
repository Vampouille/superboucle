# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'superboucle/device_manager_ui.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(320, 229)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.list = QtWidgets.QListWidget(Dialog)
        self.list.setObjectName("list")
        self.gridLayout.addWidget(self.list, 0, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.editButton = QtWidgets.QPushButton(Dialog)
        self.editButton.setObjectName("editButton")
        self.verticalLayout.addWidget(self.editButton)
        self.deleteButton = QtWidgets.QPushButton(Dialog)
        self.deleteButton.setObjectName("deleteButton")
        self.verticalLayout.addWidget(self.deleteButton)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.importButton = QtWidgets.QPushButton(Dialog)
        self.importButton.setObjectName("importButton")
        self.verticalLayout.addWidget(self.importButton)
        self.exportButton = QtWidgets.QPushButton(Dialog)
        self.exportButton.setObjectName("exportButton")
        self.verticalLayout.addWidget(self.exportButton)
        self.gridLayout.addLayout(self.verticalLayout, 0, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Manage Devices"))
        self.editButton.setText(_translate("Dialog", "Edit"))
        self.deleteButton.setText(_translate("Dialog", "Delete"))
        self.importButton.setText(_translate("Dialog", "Import"))
        self.exportButton.setText(_translate("Dialog", "Export"))

