class MidiNote:

    def __init__(self, pitch, velocity, start_tick, length) -> None:
        self.pitch = pitch           # midi pitch 0 --> C-1
        self.velocity = velocity     # in [0, 127]
        self.start_tick = start_tick # start position in tick with 24 tick per beat
        self.length = length         # note length in tick

    def __str__(self) -> str:
        note = chr(((self.pitch + 2) % 7) + (65))

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, MidiNote):
            return False
        return self.pitch == __value.pitch and self.start_tick == __value.start_tick
    
    def __hash__(self):
        return hash((self.pitch, self.start_tick))


class MidiEvents:

    def __init__(self) -> None:
        self.events = dict[int, set]
    
    def addEvent(self, tick: int, event: bytes):
        if tick in self.events.keys():
            self.events[tick].add(event)
        else:
            self.event[tick] = set(event)

    def get(self, tick: int):
        if tick in self.events.keys():
            return self.events[tick]
        else:
            return set()

    def __str__(self) -> str:
        for tick in self.events.keys():
            print("tick %s: %s" % (tick, self.get(tick).join(", ")))
        

class MidiClip:

    def __init__(self, length: int) -> None:
        self.length: int = length # in beats
        self.notes: set[MidiNote] = set()
        self.events: MidiEvents = MidiEvents()
    
    def addNote(self, note: MidiNote) -> None:
        if note in self.notes:
            self.notes.remove(note)
        self.notes.add(note)

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