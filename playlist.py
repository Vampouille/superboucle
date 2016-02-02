from PyQt5.QtWidgets import QDialog, QFileDialog, QAbstractItemView
from playlist_ui import Ui_Dialog
from clip import load_song_from_file, verify_ext
import json
from os.path import basename, splitext


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
        self.show()

    def updateList(self):
        self.playlistList.clear()
        for song in self.gui.playlist:
            name, ext = splitext(basename(song))  # song.file_name
            self.playlistList.addItem(name)

    def onRemove(self):
        id = self.playlistList.currentRow()
        if id != -1:
            del self.gui.playlist[id]
            self.updateList()

    def onMoveRows(self, sourceParent, sourceStart, sourceEnd,
                   destinationParent, destinationRow):
        l = self.gui.playlist
        destinationRow -= destinationRow > sourceStart
        l.insert(destinationRow, l.pop(sourceStart))

    def onAddSongs(self):
        file_names, a = self.gui.getOpenFileName('Add Songs',
                                                 'Super Boucle Song (*.sbs)',
                                                 self,
                                                 QFileDialog.getOpenFileNames)
        self.gui.playlist += file_names  # getSongs(file_names)
        self.updateList()

    def onLoadPlaylist(self):
        file_name, a = self.gui.getOpenFileName('Open Playlist',
                                                ('Super Boucle '
                                                 'Playlist (*.sbp)'),
                                                self)
        if not file_name:
            return
        with open(file_name, 'r') as f:
            read_data = f.read()
        self.gui.playlist = json.loads(read_data)
        self.updateList()

    def onSavePlaylist(self):
        file_name, a = self.gui.getSaveFileName('Save Playlist',
                                                ('Super Boucle '
                                                 'Playlist (*.sbp)'),
                                                self)

        if file_name:
            file_name = verify_ext(file_name, 'sbp')
            with open(file_name, 'w') as f:
                f.write(json.dumps(self.gui.playlist))

    def onLoadSong(self):
        id = self.playlistList.currentRow()
        self.loadSong(id)

    def onSongDoubleClick(self, item):
        id = self.playlistList.row(item)
        self.loadSong(id)

    def loadSong(self, id):
        if id == -1:
            return
        file_name = self.gui.playlist[id]
        try:
            self.gui.openSongFromDisk(file_name)
        except Exception as e:
            print("could not load File {}.\nError: {}".format(file_name, e))
