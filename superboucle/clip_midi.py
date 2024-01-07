class MidiNote:

    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self, pitch, velocity, start_tick, length) -> None:
        self.pitch = pitch           # midi pitch 0 --> C-1 send as is to the jack lib
        self.velocity = velocity     # in [0, 127]
        self.start_tick = start_tick # start position in tick with 24 tick per beat
        self.length = length         # note length in tick

    def __str__(self) -> str:
        return "%s%s(%s)/%s %s %s" % (self.noteName(), (self.pitch // 12) - 2, self.pitch, self.velocity, self.humanizeTickPosition(self.start_tick), self.humanizeTickDuration(self.length))
    
    def humanizeTickPosition(self, tick: int) -> str:
        beat = tick // 24
        remaining_tick = tick % 24
        bar = beat // 4
        beat %= 4

        return "%s|%s|%s" % (bar + 1, beat + 1, remaining_tick)

    def humanizeTickDuration(self, tick: int) -> str:
        beat = tick // 24
        remaining_tick = tick % 24

        return "%s.%s" % (beat, remaining_tick)


    def noteName(self) -> str:
        return MidiNote.NOTES[self.pitch % 12]

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, MidiNote):
            return False
        return self.pitch == __value.pitch and self.start_tick == __value.start_tick
    
    def __hash__(self):
        return hash((self.pitch, self.start_tick))
    
    def copy(self):
        return MidiNote(self.pitch, self.velocity, self.start_tick, self.length)


class MidiEvents:

    def __init__(self) -> None:
        self.events: dict[int, set] = {}
    
    def addEvent(self, tick: int, event: bytes):
        if tick in self.events.keys():
            self.events[tick].add(event)
        else:
            self.events[tick] = set(event)

    def get(self, tick: int):
        if tick in self.events.keys():
            return self.events[tick]
        else:
            return set()

    def __str__(self) -> str:
        for tick in self.events.keys():
            print("tick %s: %s" % (tick, self.get(tick).join(", ")))
        

class MidiClip:

    def __init__(self, length: int, channel: int) -> None:
        self.length: int = length # in beats
        self.channel: int = channel # 0-15 ?w
        self.notes: set[MidiNote] = set()
        self.events: MidiEvents = MidiEvents()
    
    def addNote(self, note: MidiNote) -> None:
        if note in self.notes:
            self.notes.remove(note)
        self.notes.add(note)

    def removeNote(self, note: MidiNote) -> None:
        self.notes.remove(note)

    def computeEvents(self) -> None:
        events = MidiEvents()
        for note in self.notes:
            events.addEvent(note.start_tick, bytes([0x90, note.pitch, note.velocity]))
            events.addEvent(note.start_tick + note.length, bytes([0x80, note.pitch, 0]))
        self.events = events

    def getEvent(self, tick: int):
        return self.events.get(tick)
        
    def __str__(self) -> str:
        res = "MIDI Events:"
        res += self.events