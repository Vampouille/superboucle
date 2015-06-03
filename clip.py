import numpy as np
import soundfile as sf
from PyQt5 import QtCore
import configparser
from zipfile import ZipFile
from io import BytesIO, StringIO, TextIOWrapper
import unicodedata


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def basename(s):
    if s is None:
        return None
    else:
        str = strip_accents(s)
        return str.split('/')[-1]


def verify_ext(file, ext):
    if file[-4:] == (".%s" % ext):
        return file
    else:
        return "%s.%s" % (file, ext)


class Communicate(QtCore.QObject):

    updateUI = QtCore.pyqtSignal()


class Clip():

    STOP = 0
    STARTING = 1
    START = 2
    STOPPING = 3
    PREPARE_RECORD = 4
    RECORDING = 5

    TRANSITION = {STOP: STARTING,
                  STARTING: STOP,
                  START: STOPPING,
                  STOPPING: START,
                  PREPARE_RECORD: RECORDING,
                  RECORDING: PREPARE_RECORD}
    RECORD_TRANSITION = {STOP: PREPARE_RECORD,
                         PREPARE_RECORD: STOP,
                         STARTING: STOP,
                         START: STOP,
                         STOPPING: STOP,
                         RECORDING: STOP}
    STATE_DESCRIPTION = {0: "STOP",
                         1: "STARTING",
                         2: "START",
                         3: "STOPPING",
                         4: "PREPARE_RECORD",
                         5: "RECORDING"}

    def __init__(self, audio_file=None, name='',
                 volume=1, frame_offset=0, beat_offset=0.0, beat_diviser=1):

        if name is '' and audio_file:
            self.name = audio_file
        else:
            self.name = name
        self.volume = volume
        self.frame_offset = frame_offset
        self.beat_offset = beat_offset
        self.beat_diviser = beat_diviser
        self.state = Clip.STOP
        self.audio_file = audio_file
        self.last_offset = 0


class Song():

    def __init__(self, width, height):
        self.clips_matrix = [[None for y in range(height)]
                             for x in range(width)]
        self.clips = []
        self.data, self.samplerate = {}, {}
        self.volume = 1.0
        self.bpm = 120
        self.beat_per_bar = 4
        self.width = width
        self.height = height
        self.file_name = None
        self.is_record = False

    def addClip(self, clip, x, y):
        if self.clips_matrix[x][y]:
            self.clips.remove(self.clips_matrix[x][y])
        self.clips_matrix[x][y] = clip
        self.clips.append(clip)
        clip.x = x
        clip.y = y

    def removeClip(self, clip):
        if clip.audio_file is not None:
            current_audio_file = clip.audio_file
            clip.audio_file = None
            if current_audio_file not in [c.audio_file for c in self.clips]:
                del self.data[current_audio_file]

        self.clips_matrix[clip.x][clip.y] = None
        self.clips.remove(clip)

    def toogle(self, x, y):
        clip = self.clips_matrix[x][y]
        if clip:
            if self.is_record:
                clip.state = Clip.RECORD_TRANSITION[clip.state]
            else:
                clip.state = Clip.TRANSITION[clip.state]

    def channels(self, clip):
        if clip.audio_file is None:
            return 0
        else:
            return self.data[clip.audio_file].shape[1]

    def length(self, clip):
        if clip.audio_file is None:
            return 0
        else:
            return self.data[clip.audio_file].shape[0]

    def get_data(self, clip, channel, offset, length):
        if clip.audio_file is None:
            return []

        channel %= self.channels(clip)
        if offset > (self.length(clip) - 1) or offset < 0 or length < 0:
            raise Exception("Invalid length or offset: {0} {1} {2}".
                            format(length, offset, self.length(clip)))
        if (length + offset) > self.length(clip):
            raise Exception("Index out of range : {0} + {1} > {2}".
                            format(length, offset, self.length(clip)))

        return (self.data[clip.audio_file][offset:offset+length, channel]
                * clip.volume)

    def write_data(self, clip, channel, offset, data):
        if clip.audio_file is None:
            raise Exception("No audio buffer available")

        if offset + data.shape[0] > self.length(clip):
            raise Exception(("attempt to write data outside of buffer"
                             ": %s + %s > %s ")
                            % (offset, data.shape[0], self.length(clip)))

        self.data[clip.audio_file][offset:offset+data.shape[0], channel] = data
        # print("Write %s bytes at offset %s to channel %s" % (data.shape[0],
        #                                                     offset,
        #                                                     channel))

    def init_record_buffer(self, clip, channel, size, samplerate):
        i = 0
        audio_file_base = basename(clip.name) or 'audio'

        # remove old audio if not used
        if clip.audio_file is not None:
            current_audio_file = clip.audio_file
            clip.audio_file = None
            if current_audio_file not in [c.audio_file for c in self.clips]:
                del self.data[current_audio_file]

        while '%s-%02d.wav' % (audio_file_base, i) in self.data:
            i += 1
        audio_file = '%s-%02d.wav' % (audio_file_base, i)
        self.data[audio_file] = np.zeros((size, channel),
                                         dtype=np.float32)
        self.samplerate[audio_file] = samplerate
        clip.audio_file = audio_file

    def save(self):
        if self.file_name:
            self.saveTo(self.file_name)
        else:
            raise Exception("No file specified")

    def saveTo(self, file):
        with ZipFile(file, 'w') as zip:
            song_file = configparser.ConfigParser()
            song_file['DEFAULT'] = {'volume': self.volume,
                                    'bpm': self.bpm,
                                    'beat_per_bar': self.beat_per_bar,
                                    'width': self.width,
                                    'height': self.height}
            for clip in self.clips:
                clip_file = {'name': clip.name,
                             'volume': str(clip.volume),
                             'frame_offset': str(clip.frame_offset),
                             'beat_offset': str(clip.beat_offset),
                             'beat_diviser': str(clip.beat_diviser),
                             'audio_file': basename(
                                 clip.audio_file)}
                if clip_file['audio_file'] is None:
                    clip_file['audio_file'] = 'no-sound'
                song_file["%s/%s" % (clip.x, clip.y)] = clip_file

            buffer = StringIO()
            song_file.write(buffer)
            zip.writestr('metadata.ini', buffer.getvalue())

            for member in self.data:
                buffer = BytesIO()
                sf.write(self.data[member], buffer,
                         self.samplerate[member],
                         subtype=sf.default_subtype('WAV'),
                         format='WAV')
                zip.writestr(member, buffer.getvalue())

        self.file_name = file


def load_song_from_file(file):
    with ZipFile(file) as zip:
        with zip.open('metadata.ini') as metadata_res:
            metadata = TextIOWrapper(metadata_res)
            parser = configparser.ConfigParser()
            parser.read_file(metadata)
            res = Song(parser['DEFAULT'].getint('width'),
                       parser['DEFAULT'].getint('height'))
            res.file_name = file
            res.volume = parser['DEFAULT'].getfloat('volume')
            res.bpm = parser['DEFAULT'].getfloat('bpm')
            res.beat_per_bar = parser['DEFAULT'].getint('beat_per_bar')

            # Loading wavs
            for member in zip.namelist():
                if member == 'metadata.ini':
                    continue
                buffer = BytesIO()
                wav_res = zip.open(member)
                buffer.write(wav_res.read())
                buffer.seek(0)
                data, samplerate = sf.read(buffer, dtype=np.float32)
                res.data[member] = data
                res.samplerate[member] = samplerate

            # loading clips
            for section in parser:
                if section == 'DEFAULT':
                    continue
                x, y = section.split('/')
                x, y = int(x), int(y)
                if parser[section]['audio_file'] == 'no-sound':
                    audio_file = None
                else:
                    audio_file = parser[section]['audio_file']
                clip = Clip(audio_file,
                            parser[section]['name'],
                            parser[section].getfloat('volume', 1.0),
                            parser[section].getint('frame_offset', 0),
                            parser[section].getfloat('beat_offset', 0.0),
                            parser[section].getint('beat_diviser'))
                res.addClip(clip, x, y)

    return res
