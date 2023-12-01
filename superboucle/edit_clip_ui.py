# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'superboucle/edit_clip_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(216, 567)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.frame_clip = QtWidgets.QFrame(Dialog)
        self.frame_clip.setGeometry(QtCore.QRect(0, 0, 216, 541))
        self.frame_clip.setStyleSheet("#frame_clip {background-color: rgb(223, 223, 223);}")
        self.frame_clip.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame_clip.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_clip.setObjectName("frame_clip")
        self.clip_name = QtWidgets.QLineEdit(self.frame_clip)
        self.clip_name.setGeometry(QtCore.QRect(0, 0, 216, 31))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.clip_name.setFont(font)
        self.clip_name.setStyleSheet("#clip_name {background-color: black; color: rgb(255, 253, 24);}")
        self.clip_name.setAlignment(QtCore.Qt.AlignCenter)
        self.clip_name.setObjectName("clip_name")
        self.label_5 = QtWidgets.QLabel(self.frame_clip)
        self.label_5.setGeometry(QtCore.QRect(20, 35, 71, 19))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.clip_volume = QSuperDial(self.frame_clip)
        self.clip_volume.setEnabled(True)
        self.clip_volume.setGeometry(QtCore.QRect(30, 55, 51, 51))
        self.clip_volume.setStyleSheet("background-color: rgb(241, 248, 0);\n"
"color: black;")
        self.clip_volume.setMaximum(256)
        self.clip_volume.setSingleStep(1)
        self.clip_volume.setObjectName("clip_volume")
        self.label_4 = QtWidgets.QLabel(self.frame_clip)
        self.label_4.setGeometry(QtCore.QRect(100, 35, 111, 19))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.beat_diviser = QtWidgets.QSpinBox(self.frame_clip)
        self.beat_diviser.setGeometry(QtCore.QRect(120, 60, 71, 41))
        self.beat_diviser.setStyleSheet("QSpinBox::up-button { width: 40px; }\n"
"QSpinBox::down-button { width: 40px; }\n"
"QSpinBox { border : 0px; border-radius: 2px}")
        self.beat_diviser.setMinimum(1)
        self.beat_diviser.setMaximum(999)
        self.beat_diviser.setObjectName("beat_diviser")
        self.deleteButton = QtWidgets.QPushButton(self.frame_clip)
        self.deleteButton.setGeometry(QtCore.QRect(99, 500, 101, 23))
        self.deleteButton.setAutoDefault(False)
        self.deleteButton.setObjectName("deleteButton")
        self.exportButton = QtWidgets.QPushButton(self.frame_clip)
        self.exportButton.setGeometry(QtCore.QRect(100, 470, 101, 23))
        self.exportButton.setAutoDefault(False)
        self.exportButton.setObjectName("exportButton")
        self.normalizeButton = QtWidgets.QPushButton(self.frame_clip)
        self.normalizeButton.setGeometry(QtCore.QRect(10, 500, 80, 23))
        self.normalizeButton.setAutoDefault(False)
        self.normalizeButton.setObjectName("normalizeButton")
        self.reverseButton = QtWidgets.QPushButton(self.frame_clip)
        self.reverseButton.setGeometry(QtCore.QRect(10, 470, 81, 23))
        self.reverseButton.setAutoDefault(False)
        self.reverseButton.setObjectName("reverseButton")
        self.groupBox = QtWidgets.QGroupBox(self.frame_clip)
        self.groupBox.setGeometry(QtCore.QRect(10, 320, 191, 51))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.mute_group = QtWidgets.QSpinBox(self.groupBox)
        self.mute_group.setGeometry(QtCore.QRect(10, 25, 43, 23))
        self.mute_group.setObjectName("mute_group")
        self.groupBox_2 = QtWidgets.QGroupBox(self.frame_clip)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 120, 191, 91))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        self.formLayoutWidget_4 = QtWidgets.QWidget(self.groupBox_2)
        self.formLayoutWidget_4.setGeometry(QtCore.QRect(10, 27, 161, 74))
        self.formLayoutWidget_4.setObjectName("formLayoutWidget_4")
        self.formLayout_4 = QtWidgets.QFormLayout(self.formLayoutWidget_4)
        self.formLayout_4.setContentsMargins(0, 0, 0, 0)
        self.formLayout_4.setObjectName("formLayout_4")
        self.frame_offset = QtWidgets.QSpinBox(self.formLayoutWidget_4)
        self.frame_offset.setMinimum(-4410000)
        self.frame_offset.setMaximum(4410000)
        self.frame_offset.setObjectName("frame_offset")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.frame_offset)
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget_4)
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        font.setItalic(True)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.label_2)
        self.beat_offset = QtWidgets.QDoubleSpinBox(self.formLayoutWidget_4)
        self.beat_offset.setEnabled(True)
        self.beat_offset.setMaximum(99.0)
        self.beat_offset.setSingleStep(0.01)
        self.beat_offset.setObjectName("beat_offset")
        self.formLayout_4.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.beat_offset)
        self.label = QtWidgets.QLabel(self.formLayoutWidget_4)
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        font.setItalic(True)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.formLayout_4.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.label)
        self.groupBox_3 = QtWidgets.QGroupBox(self.frame_clip)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 390, 191, 61))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setObjectName("groupBox_3")
        self.output = QtWidgets.QComboBox(self.groupBox_3)
        self.output.setGeometry(QtCore.QRect(10, 30, 141, 23))
        self.output.setObjectName("output")
        self.groupBox_4 = QtWidgets.QGroupBox(self.frame_clip)
        self.groupBox_4.setGeometry(QtCore.QRect(10, 230, 191, 71))
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_4.setFont(font)
        self.groupBox_4.setObjectName("groupBox_4")
        self.stretch_mode_resample = QtWidgets.QRadioButton(self.groupBox_4)
        self.stretch_mode_resample.setGeometry(QtCore.QRect(10, 48, 91, 22))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stretch_mode_resample.sizePolicy().hasHeightForWidth())
        self.stretch_mode_resample.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        self.stretch_mode_resample.setFont(font)
        self.stretch_mode_resample.setObjectName("stretch_mode_resample")
        self.stretch_mode_timestretch = QtWidgets.QRadioButton(self.groupBox_4)
        self.stretch_mode_timestretch.setGeometry(QtCore.QRect(97, 48, 101, 22))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stretch_mode_timestretch.sizePolicy().hasHeightForWidth())
        self.stretch_mode_timestretch.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        self.stretch_mode_timestretch.setFont(font)
        self.stretch_mode_timestretch.setObjectName("stretch_mode_timestretch")
        self.stretch_mode_disable = QtWidgets.QRadioButton(self.groupBox_4)
        self.stretch_mode_disable.setGeometry(QtCore.QRect(10, 23, 91, 22))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stretch_mode_disable.sizePolicy().hasHeightForWidth())
        self.stretch_mode_disable.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Lato")
        font.setPointSize(10)
        self.stretch_mode_disable.setFont(font)
        self.stretch_mode_disable.setObjectName("stretch_mode_disable")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_5.setText(_translate("Dialog", "Volume"))
        self.label_4.setText(_translate("Dialog", "Beat Amount"))
        self.deleteButton.setText(_translate("Dialog", "Delete Clip"))
        self.exportButton.setText(_translate("Dialog", "Export Sample"))
        self.normalizeButton.setText(_translate("Dialog", "Normalize"))
        self.reverseButton.setText(_translate("Dialog", "Reverse"))
        self.groupBox.setTitle(_translate("Dialog", "Mute Group"))
        self.groupBox_2.setTitle(_translate("Dialog", "Clip Offset"))
        self.label_2.setText(_translate("Dialog", "Sample"))
        self.label.setText(_translate("Dialog", "Beat"))
        self.groupBox_3.setTitle(_translate("Dialog", "Output"))
        self.groupBox_4.setTitle(_translate("Dialog", "Stretch Mode"))
        self.stretch_mode_resample.setText(_translate("Dialog", "Resample"))
        self.stretch_mode_timestretch.setText(_translate("Dialog", "TimeStretch"))
        self.stretch_mode_disable.setText(_translate("Dialog", "Disable"))
from superboucle.qsuperdial import QSuperDial
