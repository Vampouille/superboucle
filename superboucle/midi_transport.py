STOPPED = 0
RUNNING = 1
MIDI_START = b"\xfa"
MIDI_ALL_SOUND_OFF = b"\xb27b00"
MIDI_STOP = b"\xfc"
MIDI_TICK = b"\xf8"


class MidiTransport:
    def __init__(self, samplerate, blocksize):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.ticks = 0
        self.bpm = None
        self.period = None
        self.last_tick = None
        self.state = STOPPED
        pass

    def notify(self, last_frame_time, offset, in_data):
        # offset: Time (in samples) relative to the beginning of the current audio block.
        # client.last_frame_time: The precise time at the start of the current process cycle.
        if in_data == MIDI_START:
            self.state = RUNNING
            self.ticks = 0
            self.last_tick = None
            self.period = None
            self.bpm = None
            print("Midi start")
        elif in_data == MIDI_STOP:
            self.state = STOPPED
            print("Midi stop")
        elif in_data == MIDI_TICK:
            if self.last_tick:
                old_period = self.period
                self.period = last_frame_time + offset - self.last_tick
                if old_period:
                    #print("Period diff: %s" % (old_period - self.period))
                    pass
                beat_duration = (self.period * 24) / self.samplerate
                self.bpm = 60 / beat_duration
                # print("Beat duration: %s" % beat_duration)
                #print(
                #    "Ticks: %s BPM: %s offset: %s"
                #    % (self.ticks + 1, round(self.bpm, 1), offset)
                #)
            self.last_tick = last_frame_time + offset
            self.ticks += 1

    def position(self, pos):
        if self.state == STOPPED or self.ticks is None or self.last_tick is None or self.period is None:
            return None
        return (float(pos - self.last_tick) / (24 * self.period)) + (float(self.ticks) / 24)