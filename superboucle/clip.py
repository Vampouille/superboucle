import time
import numpy as np
import resampy
from pyrubberband import time_stretch

from superboucle.abstract_clip import AbstractClip

class WaveForm():
    def __init__(self, data, sr, beat_sample, effect="disable"):
        self.data = data
        self.sr = sr
        # How many sample per beat
        self.beat_sample = beat_sample
        self.effect = effect # disable, resample, timestretch
        # last sample played
        self.next_offset = 0

    def rewind(self):
        self.next_offset = 0

    def getSamples(self, length, start_pos=None, fade_in=0, fade_out=0, move_head=True):
        if start_pos is not None:
            s = start_pos
            e = start_pos + length
        else:
            s = self.next_offset 
            e = self.next_offset + length

        # Don't try to extract more sample than available
        e = min(e, self.length() - 1)
        res = self.data[s:e, :]
        if fade_in > 0:
            fade_in = min(fade_in, len(res))
            fade_factor = np.tile(np.linspace(0, 1, fade_in)[:, np.newaxis], self.data.shape[1])
            res[:fade_in] *= fade_factor
        if fade_out > 0:
            fade_out = min(fade_out, len(res))
            fade_factor = np.tile(np.linspace(1, 0, fade_out)[:, np.newaxis], self.data.shape[1])
            res[len(res) - fade_out:] *= fade_factor
        #print("(%s)%s-%s(%s)" % (fade_in, s, e, fade_out))
        if move_head:
            self.next_offset = e
        return res

    def writeSamples(self, bufferL, bufferR, start_pos=None, move_head=True):
        s = self.next_offset if start_pos is None else start_pos
        e = min(self.length(), s + len(bufferL))
        #print("WRITE: %s-%s" % (s, e))
        self.data[s:e] = np.column_stack((bufferL, bufferR))

        if move_head:
            self.next_offset = e

    def resample(self, new_beat_sample):
        start = time.time()
        new_samplerate = self.sr * (new_beat_sample / self.beat_sample)
        res = WaveForm(resampy.resample(self.data, self.sr, new_samplerate, axis=0), self.sr, new_beat_sample, "resample")
        #print("Resample: %s -> %s / %s / %s -> %s"
        #       % (self.beat_sample, new_beat_sample, new_samplerate, self.data.shape, res.data.shape))
        #print("Resample: %s" % round(1000 * (time.time() - start), 2))
        return res

    def timeStretch(self, new_beat_sample):
        return WaveForm(time_stretch(self.data, self.sr, self.beat_sample / new_beat_sample ), self.sr, new_beat_sample, "timestretch")

    def copy(self):
        return WaveForm(np.copy(self.data), self.sr, self.beat_sample, self.effect)

    def length(self):
        return self.data.shape[0]

    def channels(self):
        return self.data.shape[1]

    def normalize(self):
        absolute_val = np.absolute(self.data)
        current_level = np.ndarray.max(absolute_val)
        self.data[:] *= 1 / current_level

    def sameSetting(self, beat_sample, effect):
        return beat_sample == self.beat_sample and effect == self.effect

class Clip(AbstractClip):
    def __init__(self, audio_file=None, name='',
                 volume=1, frame_offset=0, beat_offset=0.0, length=8,
                 stretch_mode='disable', output=AbstractClip.DEFAULT_OUTPUT, mute_group=0):
        super().__init__(name, volume, length, output, mute_group)
        self.frame_offset = frame_offset
        self.beat_offset = beat_offset
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
        if self.audio_file is None:
            self.channels = 0
        else:
            self.channels = self.audio_file.channels()
        self.edit_clip = None

    def serialize(self):
        return {'type': 'audio',
                'name': self.name,
                'volume': str(self.volume),
                'frame_offset': str(self.frame_offset),
                'beat_offset': str(self.beat_offset),
                'length': str(self.length),
                'beat_sample': str(self.audio_file.beat_sample),
                'output': self.output,
                'mute_group': str(self.mute_group)
               }

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
        if self.stretch_mode == "timestretch":
            return self.audio_file.timeStretch(new_beat_sample)
        elif self.stretch_mode == "resample":
            return self.audio_file.resample(new_beat_sample)

    def changeBeatSample(self, new_beat_sample):
        if self.audio_file_id == 0:
            if self.audio_file_a is None or not self.audio_file_a.sameSetting(new_beat_sample, self.stretch_mode):
                if self.edit_clip:
                    self.edit_clip.setColor(1, "Creating")
                self.audio_file_a = self.generateNewWaveForm(new_beat_sample)
                print("Generating new WaveForm to A %s %s" % (new_beat_sample, self.stretch_mode))
            self.audio_file_next_id = 1
            if self.edit_clip:
                self.edit_clip.updateDesc(1)
                self.edit_clip.setColor(1, "Next")
        elif self.audio_file_id == 1:
            if self.audio_file_b is None or not self.audio_file_b.sameSetting(new_beat_sample, self.stretch_mode):
                if self.edit_clip:
                    self.edit_clip.setColor(2, "Creating")
                self.audio_file_b = self.generateNewWaveForm(new_beat_sample)
                print("Generating new WaveForm to B %s %s" % (new_beat_sample, self.stretch_mode))
            self.audio_file_next_id = 2
            if self.edit_clip:
                self.edit_clip.updateDesc(2)
                self.edit_clip.setColor(2, "Next")
        elif self.audio_file_id == 2:
            if self.audio_file_a is None or not self.audio_file_a.sameSetting(new_beat_sample, self.stretch_mode):
                if self.edit_clip:
                    self.edit_clip.setColor(1, "Creating")
                self.audio_file_a = self.generateNewWaveForm(new_beat_sample)
                print("Generating new WaveForm to A %s %s" % (new_beat_sample, self.stretch_mode))
            self.audio_file_next_id = 1
            if self.edit_clip:
                self.edit_clip.updateDesc(1)
                self.edit_clip.setColor(1, "Next")

    def getSamples(self, length, start_pos=None, fade_in=0, fade_out=0, move_head=True):
        data = self.getAudio().getSamples(length,
                                          start_pos,
                                          fade_in,
                                          fade_out,
                                          move_head)
        return data * self.volume

    def remainingSamples(self):
        wf = self.getAudio()
        return wf.length() - wf.next_offset

    def writeSamples(self, bufferL, bufferR, start_pos=None):
        if self.audio_file is None:
            raise Exception("No audio buffer available")

        self.getAudio().writeSamples(bufferL, bufferR, start_pos)

    def rewind(self):
        self.getAudio().rewind()

    # position relative to the clip between 0 and 1
    def getPos(self):
        if not self.audio_file:
            return 0
        else:
            return self.getAudio().next_offset / self.getAudio().length()


