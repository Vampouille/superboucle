import unicodedata
from collections import OrderedDict as OrderedDict_
import numpy as np
from zipfile import ZipFile
import configparser, json
from io import BytesIO, StringIO, TextIOWrapper
import soundfile as sf

from superboucle.clip import Clip, WaveForm
from superboucle.clip_midi import MidiClip, MidiNote
from superboucle.port import AudioPort, MidiPort

class Song():
    CHANNEL_NAMES = ["L", "R"]
    CHANNEL_NAME_PATTERN = "{port}_{channel}"

    def __init__(self, width=None, height=None, file=None):
        if file is not None:
            # Fetch song size from file
            with ZipFile(file) as zip:
                with zip.open('metadata.ini') as metadata_res:
                    metadata = TextIOWrapper(metadata_res)
                    parser = configparser.ConfigParser()
                    parser.read_file(metadata)
                    width = parser['DEFAULT'].getint('width')
                    height = parser['DEFAULT'].getint('height')
        self.clips_matrix = [[None for y in range(height)]
                             for x in range(width)]
        self.width = width
        self.height = height
        self.clips = []
        self.data, self.samplerate = {}, {}
        self.is_record = False

        if file is not None:
            # Fetch song size from file
            with ZipFile(file) as zip:
                with zip.open('metadata.ini') as metadata_res:
                    metadata = TextIOWrapper(metadata_res)
                    parser = configparser.ConfigParser()
                    parser.read_file(metadata)
                    self.file_name = file
                    self.volume = parser['DEFAULT'].getfloat('volume', 1.0)
                    self.bpm = parser['DEFAULT'].getfloat('bpm', 120.0)
                    self.beat_per_bar = parser['DEFAULT'].getint('beat_per_bar', 4)
                    self.audioRecordRegexp = parser['DEFAULT'].get('audio_record_regexp', '')
                    self.midiRecordRegexp = parser['DEFAULT'].get('midi_record_regexp', '')
                    self.midiClockRegexp = parser['DEFAULT'].get('midi_clock_regexp', '')
                    self.midiControlInputRegexp = parser['DEFAULT'].get('midi_control_intput_regexp', '')
                    self.midiControlOutputRegexp = parser['DEFAULT'].get('midi_control_output_regexp', '')
                    outputs = json.loads(parser['DEFAULT'].get('outputs', '[{"name": "%s"}]' % Clip.DEFAULT_OUTPUT))
                    midiOutputs = json.loads(parser['DEFAULT'].get('midi_outputs', '[{"name": "%s"}]' % Clip.DEFAULT_OUTPUT))

                    if len(outputs) and isinstance(outputs[0], str):
                        # Backward compatibility, before midi implementation
                        # the 'outputs' field was a json encoded list of string: "Main"
                        # now it's a list of object: {"name": "Main"}
                        self.outputsPorts = set([AudioPort(name=n) for n in outputs])
                    else:
                        self.outputsPorts = set([AudioPort(json=j) for j in outputs])
                    self.outputsMidiPorts = set([MidiPort(json=j) for j in midiOutputs])

                    scenes = parser['DEFAULT'].get('scenes', '{}')
                    jsDecoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
                    self.scenes = jsDecoder.decode(scenes)
                    self.initial_scene = parser['DEFAULT'].get('initial_scene', None)

                    # loading clips
                    for section_label in parser:
                        if section_label == 'DEFAULT':
                            continue
                        x, y = section_label.split('-')
                        x, y = int(x), int(y)

                        section = parser[section_label]
                        type = section.get('type', 'audio')

                        clip = None 

                        if type == 'midi':
                            clip = MidiClip(name=section['name'],
                                            length=section.getint('length'),
                                            channel=section.getint('channel'),
                                            volume=section.getfloat('volume'),
                                            quantize=section.getint('quantize', 24),
                                            output=section.get('output', Clip.DEFAULT_OUTPUT),
                                            mute_group=section.getint('mute_group', 0))
                            for n in json.loads(section['notes']):
                                clip.addNote(MidiNote(*n))
                            clip.computeEvents()
                        elif type == 'audio':
                            # Extract soundfile from archive
                            wav_res = zip.open("%s.wav" % section_label)
                            buffer = BytesIO()
                            buffer.write(wav_res.read())
                            buffer.seek(0)
                            data, samplerate = sf.read(buffer, dtype=np.float32, always_2d=True)

                            # Build WaveForm object
                            beat_sample = None if section.get('beat_sample') == 'None' else float(section.get('beat_sample'))
                            audio_file = WaveForm(data, samplerate, beat_sample)

                            clip = Clip(audio_file=audio_file,
                                        name=section['name'],
                                        volume=section.getfloat('volume', 1.0),
                                        frame_offset=section.getint('frame_offset', 0),
                                        beat_offset=section.getfloat('beat_offset', 0.0),
                                        length=section.getint('length'),
                                        stretch_mode=section.get('stretch_mode','disable'),
                                        output=section.get('output', Clip.DEFAULT_OUTPUT),
                                        mute_group=section.getint('mute_group', 0))
                        self.addClip(clip, x, y)
        else:
            self.volume = 1.0
            self.bpm = 120
            self.beat_per_bar = 4
            self.file_name = None
            self.outputsPorts = set()
            self.outputsPorts.add(AudioPort(name=Clip.DEFAULT_OUTPUT))
            self.outputsMidiPorts = set()
            self.outputsMidiPorts.add(MidiPort(name=Clip.DEFAULT_OUTPUT))
            self.audioRecordRegexp = ''
            self.midiRecordRegexp = ''
            self.midiClockRegexp = ''
            self.midiControlInputRegexp = ''
            self.midiControlOutputRegexp = ''
            self.scenes = OrderedDict()
            self.initial_scene = None

    # Scene management
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

    # Clip management
    def addClip(self, clip, x, y):
        if self.clips_matrix[x][y]:
            self.clips.remove(self.clips_matrix[x][y])
        self.clips_matrix[x][y] = clip
        self.clips.append(clip)
        #if isinstance(clip, MidiClip):
        #    self.outputsMidiPorts.add(MidiPort(name=clip.output))
        #else:
        #    self.outputsPorts.add(AudioPort(name=clip.output))
        clip.x = x
        clip.y = y

    def removeClip(self, clip):
        if isinstance(clip, MidiClip) and clip.audio_file is not None:
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

    def init_record_buffer(self, clip, channel, size, samplerate, beat_sample):
        clip.audio_file = WaveForm(np.zeros((size, channel), dtype=np.float32), samplerate, beat_sample, "disable")

    def removeAudioPort(self, port):
        if port.name != Clip.DEFAULT_OUTPUT:
            self.outputsPorts.remove(port)
            for c in self.clips:
                if isinstance(c, Clip) and c.output == port.name:
                    c.output = Clip.DEFAULT_OUTPUT

    def removeMidiPort(self, port):
        if port.name != Clip.DEFAULT_OUTPUT:
            self.outputsMidiPorts.remove(port)
            for c in self.clips:
                if isinstance(c, MidiClip) and c.output == port.name:
                    c.output = Clip.DEFAULT_OUTPUT

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
                                    'height': self.height,
                                    'outputs': json.dumps([p.serialize() for p in self.outputsPorts]),
                                    'midi_outputs': json.dumps([p.serialize() for p in self.outputsMidiPorts]),
                                    'audio_record_regexp': self.audioRecordRegexp,
                                    'midi_record_regexp': self.midiRecordRegexp,
                                    'midi_clock_regexp': self.midiClockRegexp,
                                    'midi_control_intput_regexp': self.midiControlInputRegexp,
                                    'midi_control_output_regexp': self.midiControlOutputRegexp,
                                    'scenes': json.dumps(self.scenes)}
            if self.initial_scene is not None:
                song_file['DEFAULT']['initial_scene'] = self.initial_scene
            for clip in self.clips:
                section = "%s-%s" % (clip.x, clip.y)
                # Write clip metadata
                song_file[section] = clip.serialize()

                if isinstance(clip, Clip):
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

class OrderedDict(OrderedDict_):
    def insert(self, key, value, index=-1):
        move_keys = list(self.keys())[index:]
        self[key] = value
        for k in move_keys:
            self.move_to_end(k)