from PyQt5.QtWidgets import QDialog, QFileDialog, QAbstractItemView
from playlist_ui import Ui_Dialog
from clip import load_song_from_file, verify_ext
import json
from os.path import expanduser, basename, splitext

def getSongs(file_names):
    return list(map(load_song_from_file, file_names))

class PlaylistDialog(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super(PlaylistDialog, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        self.updateList()
        self.removeSongBtn.clicked.connect(self.onRemove)
        self.addSongsBtn.clicked.connect(self.onAddSongs)
        self.loadPlaylistBtn.clicked.connect(self.onLoadPlaylist)
        self.savePlaylistBtn.clicked.connect(self.onSavePlaylist)
        self.loadSongBtn.clicked.connect(self.onLoadSong)
        self.playlistList.itemDoubleClicked.connect(self.onSongDoubleClick)
        self.playlistList.setDragDropMode(QAbstractItemView.InternalMove)
        self.playlistList.model().rowsMoved.connect(self.onMoveRows)
        self.finished.connect(self.onFinished)
        self.show()

    def updateList(self):
        self.playlistList.clear()
        for song in self.gui.playlist:
            name, ext = splitext(basename(song.file_name))
            self.playlistList.addItem(name)

    def onRemove(self):
        id = self.playlistList.currentRow()
        if id != -1:
            song = self.gui.playlist[id]
            self.gui.playlist.remove(song)
            self.updateList()

    def onMoveRows(self, sourceParent, sourceStart, sourceEnd, destinationParent, destinationRow):
        l = self.gui.playlist
        destinationRow -= destinationRow > sourceStart
        l.insert(destinationRow, l.pop(sourceStart))

    def onAddSongs(self):
        file_names, a = (
            QFileDialog.getOpenFileNames(self,
                                         'add Songs',
                                         expanduser('~'),
                                         'Super Boucle Song (*.sbs)'))
        self.gui.playlist += getSongs(file_names)
        self.updateList()

    def onLoadPlaylist(self):
        file_name, a = (
            QFileDialog.getOpenFileName(self,
                                        'Open file',
                                        expanduser('~'),
                                        'Super Boucle Playlist (*.sbp)'))
        if not file_name:
            return
        with open(file_name, 'r') as f:
            read_data = f.read()
        self.gui.playlist = getSongs(json.loads(read_data))
        self.updateList()

    def clearPlaylist(self):
        self.playlistList.clear()
        self.gui.playlist[:] = []

    def onSavePlaylist(self):
        file_name, a = (
            QFileDialog.getSaveFileName(self,
                                        'Save As',
                                        expanduser('~'),
                                        'Super Boucle Playlist (*.sbp)'))

        if file_name:
            file_name = verify_ext(file_name, 'sbp')
            with open(file_name, 'w') as f:
                f.write(json.dumps([song.file_name for song in self.gui.playlist]))

    def onLoadSong(self):
        id = self.playlistList.currentRow()
        self.loadSong(id)

    def onSongDoubleClick(self, item):
        id = self.playlistList.row(item)
        self.loadSong(id)

    def loadSong(self, id):
        if id != -1:
            print(id)
            song = self.gui.playlist[id]
            self.gui.initUI(song)

    def onFinished(self):
        pass
        # self.gui.updateDevices()
