import time
import threading
from threading import Thread
from collections import deque
from PyQt5.QtCore import pyqtSignal, QObject

from superboucle.clip_midi import MidiClip

STOPPED = 0
RUNNING = 1
MIDI_START = b"\xfa"
MIDI_ALL_SOUND_OFF = b"\xb27b00"
MIDI_STOP = b"\xfc"
MIDI_TICK = b"\xf8"

class MidiTransport(QObject):

    prepareNextBeatSignal = pyqtSignal(int)
    updateSyncSignal = pyqtSignal()
    updatePosSignal = pyqtSignal()
    updateClockSignal = pyqtSignal()

    def __init__(self, gui):
        QObject.__init__(self)
        super(MidiTransport, self).__init__()
        self.gui = gui
        self.ticks = 0
        self.periods = deque(maxlen=10)
        self.first_tick = None
        self.last_tick = None
        self.state = STOPPED
        self.prepareNextBeatSignal.connect(self.prepareNextBeat)
        self.updateSyncSignal.connect(self.updateSync)
        self.updatePosSignal.connect(self.updatePos)
        self.updateClockSignal.connect(self.updateClock)
        self.wip = threading.Lock()

    def getBPM(self):
        return self.gui.tick_period_to_bpm(self.periodMean())

    def periodMean(self):
        if self.gui.force_integer_bpm.isChecked():
            return self.gui.bpm_to_tick_period(round(self.gui.tick_period_to_bpm(sum(self.periods)/len(self.periods))))
        else:
            return sum(self.periods)/len(self.periods)

    def notify(self, frame_time, in_data):
        # Call in a realtime context
        #
        # return the index and offset of a tick
        #
        # offset: Time (in samples) relative to the beginning of the current audio block.
        # client.last_frame_time: The precise time at the start of the current process cycle.
        # frame_time = client.last_frame_time + offset
        if in_data == MIDI_START:
            self.state = RUNNING
            self.ticks = -1
            self.last_tick = None
            self.periods.clear()
            self.bpm = None
            self.first_tick = None
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
            self.updateClockSignal.emit()
            if tick == 0:
                self.prepareNextBeatSignal.emit(beat)
                self.updatePosSignal.emit()
            return self.ticks
        return None

    def position_sample(self, pos):
        return pos - self.first_tick

    def position_beats(self, pos):
        if self.state == STOPPED or self.ticks is None or self.last_tick is None or len(self.periods) == 0:
            return None
        return (float(pos - self.last_tick) / (24 * self.periodMean())) + (float(self.ticks) / 24)

    def prepareNextBeat(self, beat):
        if self.wip.acquire(blocking=False):
            st = time.time()
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
                    if clp is not None and not isinstance(clp, MidiClip) and clp.stretch_mode != 'disable':
                        # only trigger resample on beat just before clip start
                        if (beat + 1) % clp.beat_diviser == 0:
                            diff = clp.getNextBeatSample() - beat_sample
                            # 40 is sample diff of beat period between 250 and 251 BPM
                            if abs(diff) > 40 or clp.stretch_mode != clp.getAudio().effect:
                                #print("---------------------------------------")
                                #print("(%s) Diff: %s %s -> %s"
                                #      % (self.gui._jack_client.frame_time,
                                #         diff,
                                #         self.period_to_bpm(clp.getNextBeatSample() / 24),
                                #         self.period_to_bpm(beat_sample / 24)))
                                #print("id: %s next: %s" %(clp.audio_file_id, clp.audio_file_next_id))

                                clp.changeBeatSample(beat_sample)
                                #print("id: %s next: %s" %(clp.audio_file_id, clp.audio_file_next_id))
                                pass
            beat_duration_sec = beat_sample / self.gui.sr
            prepare_duration_sec = time.time() - st
            self.gui.prepare_duration.setValue(int((100 * prepare_duration_sec ) / beat_duration_sec))
            self.gui.prepare_duration.repaint()
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
        seconds = int((ft - self.first_tick) / self.gui.sr)
        (minutes, second) = divmod(seconds, 60)
        (hour, minute) = divmod(minutes, 60)
        time = "%d:%02d:%02d" % (hour, minute, second)
        self.gui.bbtLabel.setText("%s\n%s" % (bbt, time))
        self.gui.bpm.setValue(self.getBPM())

    def updateClock(self):
        self.gui.clock.tick = self.ticks
        self.gui.clock.update()
