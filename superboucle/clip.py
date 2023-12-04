import numpy as np
import soundfile as sf
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSignal
import configparser, json
from zipfile import ZipFile
from io import BytesIO, StringIO, TextIOWrapper
from collections import OrderedDict as OrderedDict_
import resampy
from pyrubberband import time_stretch
import unicodedata


class OrderedDict(OrderedDict_):
    def insert(self, key, value, index=-1):
        move_keys = list(self.keys())[index:]
        self[key] = value
        for k in move_keys:
            self.move_to_end(k)


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

class WaveForm():
    def __init__(self, data, sr, beat_sample):
        self.data = data
        self.sr = sr
        # How many sample per beat
        self.beat_sample = beat_sample
        # last sample played
        self.last_offset = -1

    def rewind(self):
        self.last_offset = -1

    def getSamples(self, channel, length, start_pos=None, fade_in=0, fade_out=0, move_head=True):
        # Normalize channel
        channel %= self.channels()

        if start_pos is not None:
            s = start_pos
            e = start_pos + length
        else:
            s = self.last_offset + 1
            e = self.last_offset + 1 + length

        # Don't try to extract more sample than available
        e = min(e, self.length() - 1)
        res = self.data[s:e, channel]
        if fade_in > 0:
            fade_in = min(fade_in, len(res))
            fade_factor = np.linspace(0, 1, fade_in)
            res[:fade_in] *= fade_factor
        if fade_out > 0:
            fade_out = min(fade_out, len(res))
            fade_factor = np.linspace(1, 0, fade_out)
            res[len(res) - fade_out:] *= fade_factor
        if move_head:
            self.last_offset = e
        return res

    def writeSamples(self, channel, data, start_pos=None, move_head=True):
        s = self.last_offset + 1 if start_pos is None else start_pos
        e = min(self.length(), s + len(data))
        self.data[s:e,channel % self.channels()] = data[0:e - s]
        if move_head:
            self.last_offset = e

    def resample(self, new_beat_sample):
        return WaveForm(resampy.resample(self.data, self.sr, self.sr * (new_beat_sample / self.beat_sample)), self.sr, new_beat_sample)

    def timeStretch(self, new_beat_sample):
        return WaveForm(time_stretch(self.data, self.sr, new_beat_sample / self.beat_sample), self.sr, new_beat_sample)

    def copy(self):
        return WaveForm(np.copy(self.data), self.sr, self.beat_sample)

    def length(self):
        return self.data.shape[0]

    def channels(self):
        return self.data.shape[1]

    def normalize(self):
        absolute_val = np.absolute(self.data)
        current_level = np.ndarray.max(absolute_val)
        self.data[:] *= 1 / current_level




class Clip(QObject):
    DEFAULT_OUTPUT = "Main"

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

    updateAudioSignal = pyqtSignal()

    def __init__(self, audio_file=None, name='',
                 volume=1, frame_offset=0, beat_offset=0.0, beat_diviser=8,
                 stretch_mode='disable', output=DEFAULT_OUTPUT, mute_group=0):
        QObject.__init__(self)
        self.name = name
        self.volume = volume
        self.frame_offset = frame_offset
        self.beat_offset = beat_offset
        self.beat_diviser = beat_diviser
        self.state = Clip.STOP
        # Original audio file
        self.audio_file = audio_file
        # set the audio_file attribute to use :
        # 0: self.audio_file
        # 1: self.audio_file_a
        # 2: self.audio_file_b
        self.audio_file_id = 0
        self.audio_file_a = None
        self.audio_file_b = None
        # Just use the original wav
        self.audio_file_id = 0
        self.audio_file_next_id = 0
        # Last bytes played for this clip
        self.stretch_mode = stretch_mode
        self.output = output
        self.mute_group = mute_group
        if self.audio_file is None:
            self.channels = 0
        else:
            self.channels = self.audio_file.channels()
        self.audioChangeCallbacks = []
        self.updateAudioSignal.connect(self.triggerAudioChangeCallbacks)

    def channels(self,):
        '''Return channel count for specified clip'''

    def stop(self):
        self.state = Clip.STOPPING if self.state == Clip.START \
            else Clip.STOP if self.state == Clip.STARTING \
            else self.state

    def start(self):
        self.state = Clip.STARTING if self.state == Clip.STOP \
            else Clip.START if self.state == Clip.STOPPING \
            else self.state

    def getAudio(self):
        if self.audio_file_id == 0:
            return self.audio_file
        elif self.audio_file_id == 1:
            return self.audio_file_a
        elif self.audio_file_id == 2:
            return self.audio_file_b
        else:
            return None

    def getBeatSample(self):
        return self.getAudio().beat_sample

    def getNextBeatSample(self):
        if self.audio_file_next_id == 0:
            return self.audio_file.beat_sample
        elif self.audio_file_next_id == 1:
            return self.audio_file_a.beat_sample
        elif self.audio_file_next_id == 2:
            return self.audio_file_b.beat_sample

    def generateNewWaveForm(self,new_beat_sample):
        if self.stretch_mode == "time":
            return self.audio_file.timeStretch(new_beat_sample)
        elif self.stretch_mode == "resample":
            return self.audio_file.resample(new_beat_sample)

    def changeBeatSample(self, new_beat_sample):
        if self.audio_file_id == 0:
            self.triggerAudioChangeCallbacks(1,"Creating")
            self.audio_file_a = self.generateNewWaveForm(new_beat_sample)
            self.audio_file_next_id = 1
            self.triggerAudioChangeCallbacks(1,"Next")
        elif self.audio_file_id == 1:
            self.triggerAudioChangeCallbacks(2,"Creating")
            self.audio_file_b = self.generateNewWaveForm(new_beat_sample)
            self.audio_file_next_id = 2
            self.triggerAudioChangeCallbacks(2,"Next")
        elif self.audio_file_id == 2:
            self.triggerAudioChangeCallbacks(1,"Creating")
            self.audio_file_a = self.generateNewWaveForm(new_beat_sample)
            self.audio_file_next_id = 1
            self.triggerAudioChangeCallbacks(1,"Next")

    def getSamples(self, channel, length, start_pos=None, fade_in=0, fade_out=0, move_head=True):
        data = self.getAudio().getSamples(channel,
                                          length,
                                          start_pos,
                                          fade_in,
                                          fade_out,
                                          move_head)
        return data * self.volume

    def writeSamples(self, channel, data, start_pos=None):
        if self.audio_file is None:
            raise Exception("No audio buffer available")

        self.getAudio().writeSamples(channel, data, start_pos)

    def rewind(self):
        self.getAudio().rewind()

    def registerAudioChange(self, callback):
        self.audioChangeCallbacks.append(callback)

    def unregisterAudioChange(self, callback):
        self.audioChangeCallbacks.remove(callback)

    def triggerAudioChangeCallbacks(self, a_b, msg):
        for c in self.audioChangeCallbacks:
            c(a_b, msg)
    
    # position relative to the clip between 0 and 1
    def getPos(self):
        beat_sample = self.getAudio().beat_sample
        if beat_sample is None:
            return self.getAudio().last_offset / self.getAudio().length()
        else:
            return self.getAudio().last_offset / (self.getAudio().sr * beat_sample * self.beat_diviser)
                                                  



class Song():
    CHANNEL_NAMES = ["L", "R"]
    CHANNEL_NAME_PATTERN = "{port}_{channel}"

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
        self.outputsPorts = set()
        self.outputsPorts.add(Clip.DEFAULT_OUTPUT)
        self.scenes = OrderedDict()
        self.initial_scene = None

    def addScene(self, name):
        clip_ids = [i for i, c in enumerate(self.clips) if
                    c.state == Clip.START]
        self.scenes[name] = clip_ids

    def removeScene(self, name):
        del self.scenes[name]

    def getSceneDesc(self, name):
        res = [[None for y in range(self.height)]
                    for x in range(self.width)]
        clip_ids = self.scenes[name]
        for i, c in enumerate(self.clips):
            res[c.x][c.y] = i in clip_ids
        return res

    def loadScene(self, name):
        clip_ids = self.scenes[name]
        self._loadScene(clip_ids)

    def loadSceneId(self, index):
        clip_ids = list(self.scenes.values())[index]
        self._loadScene(clip_ids)

    def _loadScene(self, clip_ids):
        for i, c in enumerate(self.clips):
            if i in clip_ids:
                c.start()
            else:
                c.stop()

    def addClip(self, clip, x, y):
        if self.clips_matrix[x][y]:
            self.clips.remove(self.clips_matrix[x][y])
        self.clips_matrix[x][y] = clip
        self.clips.append(clip)
        self.outputsPorts.add(clip.output)
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

    def toggle(self, x, y):
        clip = self.clips_matrix[x][y]
        if clip is None:
            return
        if self.is_record:
            clip.state = Clip.RECORD_TRANSITION[clip.state]
        else:
            clip.state = Clip.TRANSITION[clip.state]
            if clip.mute_group:
                for c in self.clips:
                    if c and c.mute_group == clip.mute_group and c != clip:
                        c.stop()

    def channels(self, clip):
        '''Return channel count for specified clip'''
        if clip.audio_file is None:
            return 0
        elif len(self.data[clip.audio_file].shape) == 1:
            return 1
        else:
            return self.data[clip.audio_file].shape[1]

    def length(self, clip):
        if clip.audio_file is None:
            return 0
        else:
            return self.data[clip.audio_file].shape[0]

    #def getData(self, clip, channel, offset, length):
    #    if clip.audio_file is None:
    #        return []

    #    channel %= self.channels(clip)
    #    if offset > (self.length(clip) - 1) or offset < 0 or length < 0:
    #        raise Exception("Invalid length or offset: {0} {1} {2}".
    #                        format(length, offset, self.length(clip)))
    #    if (length + offset) > self.length(clip):
    #        raise Exception("Index out of range : {0} + {1} > {2}".
    #                        format(length, offset, self.length(clip)))
    #    if self.channels(clip) == 1:
    #        res = np.squeeze(self.data[clip.audio_file][offset:offset + length])
    #    else:
    #        res = np.squeeze(self.data[clip.audio_file][offset:offset + length, channel])
    #    return res * clip.volume

    #def writeData(self, clip, channel, offset, data):
    #    if clip.audio_file is None:
    #        raise Exception("No audio buffer available")

    #    if offset + data.shape[0] > self.length(clip):
    #        data = data[0:data.shape[0] - 2]
    #        # raise Exception(("attempt to write data outside of buffer"
    #        #                 ": %s + %s > %s ")
    #        #                % (offset, data.shape[0], self.length(clip)))

    #    self.data[clip.audio_file][offset:offset + data.shape[0],
    #    channel] = data
    #    # print("Write %s bytes at offset %s to channel %s" % (data.shape[0],
    #    # offset,
    #    # channel))

    def init_record_buffer(self, clip, channel, size, samplerate, beat_sample):
        clip.audio_file = WaveForm(np.zeros((size, channel), dtype=np.float32), samplerate, beat_sample)


    def save(self):
        if self.file_name:
            self.saveTo(self.file_name)
        else:
            raise Exception("No file specified")

    def saveTo(self, file):
        with ZipFile(file, 'w') as zip:
            song_file = configparser.ConfigParser()
            port_list = list(self.outputsPorts)
            song_file['DEFAULT'] = {'volume': self.volume,
                                    'bpm': self.bpm,
                                    'beat_per_bar': self.beat_per_bar,
                                    'width': self.width,
                                    'height': self.height,
                                    'outputs': json.dumps(port_list),
                                    'scenes': json.dumps(self.scenes)}
            if self.initial_scene is not None:
                song_file['DEFAULT']['initial_scene'] = self.initial_scene
            for clip in self.clips:
                section = "%s-%s" % (clip.x, clip.y)
                # Write clip metadata
                clip_file = {'name': clip.name,
                             'volume': str(clip.volume),
                             'frame_offset': str(clip.frame_offset),
                             'beat_offset': str(clip.beat_offset),
                             'beat_diviser': str(clip.beat_diviser),
                             'beat_sample': str(clip.audio_file.beat_sample),
                             'output': clip.output,
                             'mute_group': str(clip.mute_group)
                             }
                song_file[section] = clip_file

                # Write clip soundfile to the archive
                buffer = BytesIO()
                sf.write(buffer, clip.audio_file.data,
                         clip.audio_file.sr,
                         subtype=sf.default_subtype('WAV'),
                         format='WAV')
                zip.writestr("%s.wav" % section, buffer.getvalue())


            # Store metadata.ini in archive
            buffer = StringIO()
            song_file.write(buffer)
            zip.writestr('metadata.ini', buffer.getvalue())


def load_song_from_file(file):
    with ZipFile(file) as zip:
        with zip.open('metadata.ini') as metadata_res:
            metadata = TextIOWrapper(metadata_res)
            parser = configparser.ConfigParser()
            parser.read_file(metadata)
            res = Song(parser['DEFAULT'].getint('width'),
                       parser['DEFAULT'].getint('height'))
            res.file_name = file
            res.volume = parser['DEFAULT'].getfloat('volume', 1.0)
            res.bpm = parser['DEFAULT'].getfloat('bpm', 120.0)
            res.beat_per_bar = parser['DEFAULT'].getint('beat_per_bar', 4)
            outputs = parser['DEFAULT'].get('outputs', '["%s"]'
                                            % Clip.DEFAULT_OUTPUT)
            res.outputsPorts = set(json.loads(outputs))

            scenes = parser['DEFAULT'].get('scenes', '{}')
            jsDecoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
            res.scenes = jsDecoder.decode(scenes)
            res.initial_scene = parser['DEFAULT'].get('initial_scene', None)

            # loading clips
            for section_label in parser:
                if section_label == 'DEFAULT':
                    continue
                x, y = section_label.split('-')
                x, y = int(x), int(y)

                # Extract soundfile from archive
                wav_res = zip.open("%s.wav" % section_label)
                buffer = BytesIO()
                buffer.write(wav_res.read())
                buffer.seek(0)
                data, samplerate = sf.read(buffer, dtype=np.float32, always_2d=True)

                section = parser[section_label]
                # Build WaveForm object
                beat_sample = None if section.get('beat_sample') == 'None' else float(section.get('beat_sample'))
                audio_file = WaveForm(data,
                                      samplerate,
                                      beat_sample)

                clip = Clip(audio_file=audio_file,
                            name=section['name'],
                            volume=section.getfloat('volume', 1.0),
                            frame_offset=section.getint('frame_offset', 0),
                            beat_offset=section.getfloat('beat_offset', 0.0),
                            beat_diviser=section.getint('beat_diviser'),
                            stretch_mode=section.get('stretch_mode','disable'),
                            output=section.get('output', Clip.DEFAULT_OUTPUT),
                            mute_group=section.getint('mute_group', 0))
                res.addClip(clip, x, y)

    return res
