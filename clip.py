import numpy as np
import soundfile as sf


class Clip():

    STOP = 0
    STARTING = 1
    START = 2
    STOPPING = 3

    def __init__(self, audio_file,
                 volume=1, frame_offset=0, beat_offset=0.0, beat_diviser=1):

        self.volume = volume
        self.frame_offset = frame_offset
        self.beat_offset = beat_offset
        self.beat_diviser = beat_diviser
        self.state = Clip.STARTING
        self.data, self.samplerate = sf.read(audio_file, dtype=np.float32)
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
        self.clips_matrix = [[None] * height] * width
        self.clips = []
        self.volume = 1.0

    def add_clip(self, clip, x, y):

        if self.clips_matrix[x][y]:
            self.clips.remove(self.clips_matrix[x][y])

        self.clips_matrix[x][y] = clip
        self.clips.append(clip)

        
