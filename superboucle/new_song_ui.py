# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'superboucle/new_song_ui.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.WindowModal)
        Dialog.resize(188, 141)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(10, 100, 166, 23))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayoutWidget = QtWidgets.QWidget(Dialog)
        self.formLayoutWidget.setGeometry(QtCore.QRect(30, 20, 101, 61))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.formLayoutWidget)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.widthSpinBox = QtWidgets.QSpinBox(self.formLayoutWidget)
        self.widthSpinBox.setMaximum(16)
        self.widthSpinBox.setProperty("value", 8)
        self.widthSpinBox.setObjectName("widthSpinBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.widthSpinBox)
        self.heightSpinBox = QtWidgets.QSpinBox(self.formLayoutWidget)
        self.heightSpinBox.setMaximum(16)
        self.heightSpinBox.setProperty("value", 8)
        self.heightSpinBox.setObjectName("heightSpinBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.heightSpinBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "New Song"))
        self.label.setText(_translate("Dialog", "Width"))
        self.label_2.setText(_translate("Dialog", "Height"))

