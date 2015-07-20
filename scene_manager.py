from PyQt5.QtWidgets import QDialog, QFileDialog, QAbstractItemView
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
        self.show()

    def updateList(self):
        self.scenelistList.clear()
        for scene in self.gui.song.scenes:
            self.scenelistList.addItem(scene)

    def onRemove(self):
        item = self.scenelistList.currentItem()
        self.gui.song.removeScene(item.text())
        self.updateList()

    def onMoveRows(self, sourceParent, sourceStart, sourceEnd,
                   destinationParent, destinationRow):
        l = self.gui.playlist
        destinationRow -= destinationRow > sourceStart
        l.insert(destinationRow, l.pop(sourceStart))

    def onAddScene(self):
        AddSceneDialog(self.gui, callback=self.updateList)

    def onLoadScene(self):
        item = self.scenelistList.currentItem()
        self.loadScene(item.text())
        self.gui.update()

    def onSceneDoubleClick(self, item):
        self.loadScene(item.text())
        self.gui.update()

    def loadScene(self, scene):
        try:
            self.gui.song.loadScene(scene)
        except:
            pass
