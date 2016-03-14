# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scene_manager_ui.ui'
#
# Created: Mon Mar 14 12:27:24 2016
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(320, 333)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.scenelistList = QtWidgets.QListWidget(Dialog)
        self.scenelistList.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.scenelistList.setSizeIncrement(QtCore.QSize(100, 100))
        self.scenelistList.setMovement(QtWidgets.QListView.Static)
        self.scenelistList.setResizeMode(QtWidgets.QListView.Adjust)
        self.scenelistList.setObjectName("scenelistList")
        self.horizontalLayout.addWidget(self.scenelistList)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.loadScenesBtn = QtWidgets.QPushButton(Dialog)
        self.loadScenesBtn.setObjectName("loadScenesBtn")
        self.verticalLayout_3.addWidget(self.loadScenesBtn)
        self.addScenesBtn = QtWidgets.QPushButton(Dialog)
        self.addScenesBtn.setObjectName("addScenesBtn")
        self.verticalLayout_3.addWidget(self.addScenesBtn)
        self.removeScenesBtn = QtWidgets.QPushButton(Dialog)
        self.removeScenesBtn.setObjectName("removeScenesBtn")
        self.verticalLayout_3.addWidget(self.removeScenesBtn)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.setInitialSceneBtn = QtWidgets.QPushButton(Dialog)
        self.setInitialSceneBtn.setObjectName("setInitialSceneBtn")
        self.verticalLayout_3.addWidget(self.setInitialSceneBtn)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Scene Manager"))
        self.loadScenesBtn.setText(_translate("Dialog", "Load Scene"))
        self.addScenesBtn.setText(_translate("Dialog", "Add Scene"))
        self.removeScenesBtn.setText(_translate("Dialog", "Remove Scene"))
        self.setInitialSceneBtn.setText(_translate("Dialog", "Set initial Scene"))

