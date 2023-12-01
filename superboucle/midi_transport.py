import time
from threading import Thread
from collections import deque
from PyQt5.QtCore import pyqtSignal, QObject

STOPPED = 0
RUNNING = 1
MIDI_START = b"\xfa"
MIDI_ALL_SOUND_OFF = b"\xb27b00"
MIDI_STOP = b"\xfc"
MIDI_TICK = b"\xf8"

class MidiTransport(QObject):
    
    prepareNextBeatSignal = pyqtSignal()
    updateSyncSignal = pyqtSignal()
    updatePosSignal = pyqtSignal()


    def __init__(self, gui, samplerate, blocksize):
        QObject.__init__(self)
        super(MidiTransport, self).__init__()
        self.gui = gui
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.ticks = 0
        self.beat_per_bar = 4
        self.periods = deque(maxlen=10)
        self.last_tick = None
        self.state = STOPPED
        self.prepareNextBeatSignal.connect(self.prepareNextBeat)
        self.updateSyncSignal.connect(self.updateSync)
        self.updatePosSignal.connect(self.updatePos)

    def getBPM(self):
        beat_duration = (self.periodMean() * 24) / self.samplerate
        return 60 / beat_duration

    def periodMean(self):
        return sum(self.periods)/len(self.periods)

    def notify(self, frame_time, in_data):
        # Call in a realtime context
        #
        # return True for a tick correpsonding to a beat
        #
        # offset: Time (in samples) relative to the beginning of the current audio block.
        # client.last_frame_time: The precise time at the start of the current process cycle.
        # frame_time = client.last_frame_time + offset
        if in_data == MIDI_START:
            self.state = RUNNING
            self.ticks = 0
            self.last_tick = None
            self.periods = deque(maxlen=10)
            self.bpm = None
            self.first_tick = None
            self.prepareNextBeatSignal.emit()
            self.updateSyncSignal.emit()
        elif in_data == MIDI_STOP:
            self.state = STOPPED
            self.updateSyncSignal.emit()
        elif in_data == MIDI_TICK:
            if self.last_tick:
                self.periods.append(frame_time - self.last_tick)
            self.last_tick = frame_time
            if self.first_tick is None:
                self.first_tick = frame_time
            self.ticks += 1
            # trigger resample or timestratch every beat for the next beat
            # Compute during current beat, Use on next beat
            if self.ticks % 24 == 0:
                self.prepareNextBeatSignal.emit()
                self.updatePosSignal.emit()
                return True
        return False

    def position_sample(self, pos):
        return pos - self.first_tick

    def position_beats(self, pos):
        if self.state == STOPPED or self.ticks is None or self.last_tick is None or len(self.periods) == 0:
            return None
        return (float(pos - self.last_tick) / (24 * self.periodMean())) + (float(self.ticks) / 24)

    def prepareNextBeat(self):
        # Wait for enough MIDI ticks
        while len(self.periods) < 10:
            # Wait 10ms
            # Receving 10 ticks took between 70ms and 800ms
            time.sleep(10/1000)
        # Compute beat duration in sample based on current tempo
        beat_sample = 24 * self.periodMean()
        # Iterate over clip
        for x in range(len(self.gui.song.clips_matrix)):
            line = self.gui.song.clips_matrix[x]
            for y in range(len(line)):
                clp = line[y]
                if clp is not None and clp.stretch_mode != 'disable':
                    diff = clp.getBeatSample() - beat_sample
                    print("Diff: %s" % diff)
                    # 5 sample of diff after 16 beat mean ~ 100ms of drift
                    if (clp.getBeatSample() - beat_sample) > 5:
                        clp.changeBeatSample(beat_sample)
    
    def updateSync(self):
        if self.state == RUNNING:
            self.gui.sync_midi.setChecked(True)
        elif self.state == STOPPED:
            self.gui.sync_mmidi.setChecked(False)

    def updatePos(self):
        beat = self.ticks / 24
        bar = beat / self.beat_per_bar
        beat %= self.beat_per_bar
        bbt = "%d|%d|%03d" % (bar, beat, 0)
        _, pos = self.gui._jack_client.transport_query()
        seconds = int((pos['frame'] - self.first_tick) / pos['frame_rate'])
        (minutes, second) = divmod(seconds, 60)
        (hour, minute) = divmod(minutes, 60)
        time = "%d:%02d:%02d" % (hour, minute, second)
        self.gui.bbtLabel.setText("%s\n%s" % (bbt, time))