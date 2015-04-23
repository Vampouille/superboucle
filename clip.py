import numpy as np
import soundfile as sf
from PyQt5 import QtCore
import configparser

class Communicate(QtCore.QObject):

    updateUI = QtCore.pyqtSignal()


class Clip():

    STOP = 0
    STARTING = 1
    START = 2
    STOPPING = 3

    TRANSITION = {STOP: STARTING,
                  STARTING: STOP,
                  START: STOPPING,
                  STOPPING: START}
    STATE_DESCRIPTION = {0: "STOP",
                         1: "STARTING",
                         2: "START",
                         3: "STOPPING"}

    def __init__(self, audio_file, name=None,
                 volume=1, frame_offset=0, beat_offset=0.0, beat_diviser=1):

        if name is None:
            self.name = audio_file
        else:
            self.name = name
        self.volume = volume
        self.frame_offset = frame_offset
        self.beat_offset = beat_offset
        self.beat_diviser = beat_diviser
        self.state = Clip.STOP
        self.audio_file = audio_file
        self.data, self.samplerate = sf.read(audio_file, dtype=np.float32)
        self.last_offset = 0
        if self.length == 0:
            raise Exception("audio file without sample!")

    @property
    def channels(self):
        return self.data.shape[1]

    @property
    def length(self):
        return self.data.shape[0]

    def get_data(self, channel, offset, length):
        channel %= self.channels
        if offset > (self.length - 1) or offset < 0 or length < 0:
            raise Exception("Invalid length or offset: {0} {1} {2}".
                            format(length, offset, self.length))
        if (length + offset) > self.length:
            raise Exception("Index out of range : {0} + {1} > {2}".
                            format(length, offset, self.length))

        return self.data[offset:offset+length, channel] * self.volume


class Song():

    def __init__(self, width, height):
        self.clips_matrix = [[None for x in range(height)]
                             for x in range(width)]
        self.clips = []
        self.volume = 1.0
        self.width = width
        self.height = height
        self.file_name = None
        self.c = Communicate()

    def add_clip(self, clip, x, y):
        if self.clips_matrix[x][y]:
            self.clips.remove(self.clips_matrix[x][y])
        self.clips_matrix[x][y] = clip
        self.clips.append(clip)
        clip.x = x
        clip.y = y

    def toogle(self, x, y):
        clip = self.clips_matrix[x][y]
        if clip:
            clip.state = Clip.TRANSITION[clip.state]
            self.c.updateUI.emit()
    
    def updateUI(self):
        self.c.updateUI.emit()

    def registerUI(self, gui_callback):
        self.c.updateUI.connect(gui_callback)

    def save(self):
        if self.file_name:
            self.saveTo(self.file_name)

    def saveTo(self, file):
        song_file = configparser.ConfigParser()
        song_file['DEFAULT'] = {'volume': self.volume,
                                'width': self.width,
                                'height': self.height}
        for clip in self.clips:
            song_file[clip.name] = {'volume': clip.volume,
                                    'frame_offset': clip.frame_offset,
                                    'beat_offset': clip.beat_offset,
                                    'beat_diviser': clip.beat_diviser,
                                    'audio_file': clip.audio_file,
                                    'x': clip.x,
                                    'y': clip.y}
        with open(file, 'w') as file_res:
            song_file.write(file_res)
        self.file_name = file


def load_song_from_file(file):
    song_file = configparser.ConfigParser()
    song_file.read(file)
    res = Song(song_file['DEFAULT'].getint('width'),
               song_file['DEFAULT'].getint('height'))
    res.file_name = file
    res.volume = song_file['DEFAULT'].getfloat('volume')
    for section in song_file:
        if section == 'DEFAULT':
            continue
        clip = Clip(song_file[section]['audio_file'],
                    section,
                    song_file[section].getfloat('volume', 1.0),
                    song_file[section].getint('frame_offset', 0),
                    song_file[section].getfloat('beat_offset', 0.0),
                    song_file[section].getint('beat_diviser'))
        res.add_clip(clip,
                     song_file[section].getint('x'),
                     song_file[section].getint('y'))
    return res




