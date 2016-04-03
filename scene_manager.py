from PyQt5.QtWidgets import QDialog, QAbstractItemView, QListWidgetItem, QFrame
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize
from scene_manager_ui import Ui_Dialog
from add_scene import AddSceneDialog
from clip import load_song_from_file

def getScenes(file_names):
    r = []
    for f in file_names:
        try:
            r.append(load_song_from_file(f))
        except Exception as e:
            print("could not load File {}.\nError: {}".format(f, e))
    return r


class SceneManager(QDialog, Ui_Dialog):
    ITEM_IT_ROLE = 100

    def __init__(self, parent):
        super(SceneManager, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.updateList()
        self.removeScenesBtn.clicked.connect(self.onRemove)
        self.addScenesBtn.clicked.connect(self.onAddScene)
        self.loadScenesBtn.clicked.connect(self.onLoadScene)
        self.scenelistList.itemDoubleClicked.connect(self.onSceneDoubleClick)
        self.scenelistList.setDragDropMode(QAbstractItemView.InternalMove)
        self.scenelistList.model().rowsMoved.connect(self.onMoveRows)
        self.scenelistList.currentItemChanged.connect(self.onCurrentItemChanged)
        self.setInitialSceneBtn.clicked.connect(self.onSetInitial)
        self.gui.songLoad.connect(self.updateList)
        self.initPreview()
        self.show()

    def updateList(self):
        self.scenelistList.clear()
        for i, scene in enumerate(self.gui.song.scenes):
            item = QListWidgetItem('{}. {}'.format(i + 1, scene))
            item.setData(self.ITEM_IT_ROLE, i)
            if self.gui.song.initial_scene == scene:
                item.setBackground(QColor('red'))
            self.scenelistList.addItem(item)
        anyScenes = bool(self.gui.song.scenes)
        self.loadScenesBtn.setEnabled(anyScenes)
        self.removeScenesBtn.setEnabled(anyScenes)
        self.initPreview()

    def initPreview(self):
        self.previewcells = [[None for y in range(self.gui.song.height)]
                             for x in range(self.gui.song.width)]
        
        for i in reversed(range(self.preview.count())):
            self.preview.itemAt(i).widget().close()
            self.preview.itemAt(i).widget().setParent(None)
            
        for y in range(self.gui.song.height):
            for x in range(self.gui.song.width):
                self.previewcells[x][y] = QFrame(self)
                self.previewcells[x][y].setMinimumSize(QSize(10, 10))
                self.previewcells[x][y].setStyleSheet("background-color: rgb(217, 217, 217);")
                self.preview.addWidget(self.previewcells[x][y], y, x, 1, 1)

    def _getSceneName(self, item):
        return list(self.gui.song.scenes.keys())[item.data(self.ITEM_IT_ROLE)]

    def onRemove(self):
        item = self.scenelistList.currentItem()
        if item:
            self.gui.song.removeScene(self._getSceneName(item))
            self.updateList()

    def onMoveRows(self, sourceParent, sourceStart, sourceEnd,
                   destinationParent, destinationRow):
        l = self.gui.song.scenes
        k, v = list(l.items())[sourceStart]
        del l[k]
        destinationRow -= destinationRow > sourceStart
        l.insert(k, v, destinationRow)
        self.updateList()

    def onAddScene(self):
        AddSceneDialog(self.gui, callback=self.updateList)

    def onSetInitial(self):
        item = self.scenelistList.currentItem()
        if item:
            self.gui.song.initial_scene = self._getSceneName(item)
            self.updateList()

    def onLoadScene(self):
        item = self.scenelistList.currentItem()
        if item:
            self.loadScene(self._getSceneName(item))
            self.gui.update()

    def onSceneDoubleClick(self, item):
        self.loadScene(self._getSceneName(item))
        self.gui.update()
        
    def onCurrentItemChanged(self, item):
        
        if item is not None:
            scene = self.gui.song.getSceneDesc(item.text())
            for x in range(len(scene)):
                line = scene[x]
                for y in range(len(line)):
                    cell = self.previewcells[x][y]
                    if line[y] is None:
                        cell.setStyleSheet("background-color: rgb(217, 217, 217);")
                    elif line[y]:
                        cell.setStyleSheet("background-color: rgb(125,242,0);")
                    else:
                        cell.setStyleSheet("background-color: rgb(255, 21, 65);")

    def loadScene(self, scene):
        try:
            self.gui.song.loadScene(scene)
        except:
            pass
