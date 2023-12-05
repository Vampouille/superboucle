import time
import threading
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
        self.periods = deque(maxlen=10)
        self.first_tick = None
        self.last_tick = None
        self.state = STOPPED
        self.prepareNextBeatSignal.connect(self.prepareNextBeat)
        self.updateSyncSignal.connect(self.updateSync)
        self.updatePosSignal.connect(self.updatePos)
        self.wip = threading.Lock()

    def bpm_to_period(self, bpm):
        return (60 * self.samplerate) / (bpm * 24)

    def period_to_bpm(self, period):
        return (60 * self.samplerate) / (period * 24)

    def getBPM(self):
        return self.period_to_bpm(self.periodMean())

    def periodMean(self):
        if self.gui.force_integer_bpm.isChecked():
            return self.bpm_to_period(round(self.period_to_bpm(sum(self.periods)/len(self.periods))))
        else:
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
            self.ticks = -1
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
            beat, tick = divmod(self.ticks, 24)
            if tick == 0:
                self.prepareNextBeatSignal.emit()
                self.updatePosSignal.emit()
                return beat
        return -1

    def position_sample(self, pos):
        return pos - self.first_tick

    def position_beats(self, pos):
        if self.state == STOPPED or self.ticks is None or self.last_tick is None or len(self.periods) == 0:
            return None
        return (float(pos - self.last_tick) / (24 * self.periodMean())) + (float(self.ticks) / 24)

    def prepareNextBeat(self):
        if self.wip.acquire(blocking=False):
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
                    if clp is not None and clp.stretch_mode != 'disable' and clp.audio_file_id == clp.audio_file_next_id:
                        diff = clp.getNextBeatSample() - beat_sample
                        # 5 sample of diff after 16 beat mean ~ 100ms of drift
                        if abs(diff) > 200:
                            print("---------------------------------------")
                            print("(%s) Diff: %s %s -> %s" 
                                  % (self.gui._jack_client.frame_time,
                                     diff,
                                     self.period_to_bpm(clp.getNextBeatSample() / 24),
                                     self.period_to_bpm(beat_sample / 24)))
                            print("id: %s next: %s" %(clp.audio_file_id, clp.audio_file_next_id))

                            clp.changeBeatSample(beat_sample)
                            print("id: %s next: %s" %(clp.audio_file_id, clp.audio_file_next_id))
            self.wip.release()
        else:
            print("Process Overlap")

    def updateSync(self):
        if self.state == RUNNING:
            self.gui.sync_source_label.setText("MIDI")
            self.gui.sync_source = 1
        elif self.state == STOPPED:
            self.gui.sync_source_label.setText("JACK")
            self.gui.sync_source = 0

    def updatePos(self):
        beat, tick = divmod(self.ticks, 24)
        bar = beat / self.gui.beat_per_bar.value()
        beat %= self.gui.beat_per_bar.value()
        bbt = "%d|%d|%03d" % (bar + 1, beat + 1, tick)
        ft = self.gui._jack_client.frame_time
        seconds = int((ft - self.first_tick) / self.samplerate)
        (minutes, second) = divmod(seconds, 60)
        (hour, minute) = divmod(minutes, 60)
        time = "%d:%02d:%02d" % (hour, minute, second)
        self.gui.bbtLabel.setText("%s\n%s" % (bbt, time))
        self.gui.bpm.setValue(self.getBPM())
