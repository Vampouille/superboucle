import time
import threading
import struct
from threading import Thread
from collections import deque
from PyQt5.QtCore import pyqtSignal, QObject

from superboucle.clip_midi import MidiClip, MidiNote

STOPPED = 0
RUNNING = 1
MIDI_START = b"\xfa"
MIDI_ALL_SOUND_OFF = b"\xb27b00"
MIDI_STOP = b"\xfc"
MIDI_TICK = b"\xf8"
TICKS_PER_BEAT = 24
MIDI_NOTE_ON = 0x9
MIDI_NOTE_OFF = 0x8

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
        self.note_recorded: dict = {}

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

    # Return samples count since Midi clock start
    # pos: position in samples absolute
    def position_sample(self, pos):
        return pos - self.first_tick

    # Compute position of pos in the midi clock
    # pos : absolute position in samples
    # return position in beat with decimal
    # accuracy is better with pos after last tick
    def position_beats(self, pos):
        if self.state == STOPPED or self.ticks is None or self.last_tick is None or len(self.periods) == 0:
            return 0
        # Compute offset since last tick
        pos_offset_samples = pos - self.last_tick
        pos_offset_beat = pos_offset_samples / (TICKS_PER_BEAT * self.periodMean())
        return self.ticks / 24 + pos_offset_beat

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
                        if (beat + 1) % clp.length == 0:
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
        if self.state == RUNNING:
            beats, tick = divmod(self.ticks, 24)
            bar, beat = divmod(beats, self.gui.beat_per_bar.value())
            bbt = "%d|%d|%03d" % (bar + 1, beat + 1, tick)
            ft = self.gui._jack_client.frame_time
            seconds = int((ft - self.first_tick) / self.gui.sr)
            (minutes, second) = divmod(seconds, 60)
            (hour, minute) = divmod(minutes, 60)
            time = "%d:%02d:%02d" % (hour, minute, second)
            self.gui.bbtLabel.setText("%s\n%s" % (bbt, time))
            self.gui.bpm.setValue(self.getBPM())
            self.updateMidiPos(bar, beat, tick)
    
    def updateMidiPos(self, bar, beat, tick):
        if tick == 0: # 4/8/16/32
          g_pos, r_pos = divmod((self.gui.beat_per_bar.value() * bar + beat) % 32, 8)
          g_pos = g_pos * 2 + (r_pos // 4)
          colors = [self.gui.device.black_vel if i > g_pos else self.gui.device.green_vel for i in range(8)]
          colors[r_pos] = self.gui.device.red_vel
          for i, color in enumerate(colors):
            self.gui.queue_out.put((0xB0, 0x68 + i , color))

    def updateClock(self):
        if self.state == RUNNING:
            self.gui.clock.tick = self.ticks
            self.gui.clock.update()

    def record(self, pos, indata, clip):
        if len(indata) == 3:
            status, pitch, vel = struct.unpack('3B', indata)
            msg_type = status >> 4

            pos = self.position_beats(pos)
            pos %= clip.length

            # Convert from beat to tick
            pos *= TICKS_PER_BEAT

            # Apply quantization
            tick_round = (24 / clip.quantize)
            pos = round(pos / tick_round) * tick_round

            if msg_type == MIDI_NOTE_ON:
                self.note_recorded[pitch] = (pos, vel)
                print(f"Record: Note On pitch={pitch} vel={vel} pos={pos}")
            elif msg_type == MIDI_NOTE_OFF:
                if pitch in self.note_recorded:
                    start_pos, vel = self.note_recorded[pitch]
                    del self.note_recorded[pitch]
                    note = MidiNote(pitch, vel, start_pos, pos - start_pos)
                    clip.addNote(note)
                    print(f"Record: Note Off pitch={pitch} pos={pos}")
                    print(f"Record adding Note: {note}")

    def stopRecord(self, pos, clip):
        pos = self.position_beats(pos)
        pos %= clip.length

        # Apply quantization
        pos *= TICKS_PER_BEAT
        pos = round(pos / clip.quantize) * clip.quantize

        for pitch, (start_pos, vel) in self.note_recorded.items():
            note = MidiNote(pitch, vel, start_pos, (pos - start_pos) % (clip.length * TICKS_PER_BEAT))
            clip.addNote(note)
            print(f"Record Stoped adding Note: {note}")
        self.note_recorded.clear()