from PyQt5.QtWidgets import QDialog, QFileDialog
from playlist_ui import Ui_Dialog
from clip import load_song_from_file, verify_ext
import json
from os.path import expanduser


class PlaylistDialog(QDialog, Ui_Dialog):

    def __init__(self, parent):
        super(PlaylistDialog, self).__init__(parent)
        self.gui = parent
        self.setupUi(self)
        for song in self.gui.playlist:
            self.playlistList.addItem(song.file_name)
        self.removeSongBtn.clicked.connect(self.onRemove)
        self.addSongsBtn.clicked.connect(self.onAddSongs)
        self.loadPlaylistBtn.clicked.connect(self.onLoadPlaylist)
        self.savePlaylistBtn.clicked.connect(self.onSavePlaylist)
        self.loadSongBtn.clicked.connect(self.onLoadSong)
        self.finished.connect(self.onFinished)
        self.show()

    def onRemove(self):
        if self.playlistList.currentRow() != -1:
            song = self.gui.playlist[self.playlistList.currentRow()]
            self.gui.playlist.remove(song)
            self.playlistList.takeItem(self.playlistList.currentRow())

    def onAddSongs(self):
        file_names, a = (
            QFileDialog.getOpenFileNames(self,
                                        'add Songs',
                                        expanduser('~'),
                                        'Super Boucle Song (*.sbs)'))
        for file_name in file_names:
            self.loadSong(file_name)

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
        playlist = json.loads(read_data)
        self.clearPlaylist()
        for file_name in playlist:
            self.loadSong(file_name)

    def loadSong(self, file_name):
        self.playlistList.addItem(file_name)
        self.gui.playlist.append(load_song_from_file(file_name))

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
        if self.playlistList.currentRow() != -1:
            song = self.gui.playlist[self.playlistList.currentRow()]
            self.gui.initUI(song)

    def onFinished(self):
        pass
        #self.gui.updateDevices()