from jack import _lib, JackError


class Transport():

    """Representation of the Jack transport state and position"""

    # transport state values
    STOPPED = _lib.JackTransportStopped
    ROLLING = _lib.JackTransportRolling
    LOOPING = _lib.JackTransportLooping
    STARTING = _lib.JackTransportStarting
    NETSTARTING = _lib.JackTransportNetStarting

    # Transport position valid fields flags
    BBT = 0x10
    TIMECODE = 0x20
    BBTFRAMEOFFSET = 0x40

    def __init__(self, transport_state, cffi_position):
        self._state = transport_state
        self._position = cffi_position

    @property
    def state(self):
        """Current state of transport."""
        return self._state

    # Position getters
    @property
    def usecs(self):
        return self._position.usecs

    @property
    def frame_rate(self):
        return self._position.frame_rate

    @property
    def frame(self):
        return self._position.frame

    @property
    def valid(self):
        return self._position.valid

    @property
    def bar(self):
        return self._position.bar

    @property
    def beat(self):
        return self._position.beat

    @property
    def tick(self):
        return self._position.tick

    @property
    def bar_start_tick(self):
        return self._position.bar_start_tick

    @property
    def beats_per_bar(self):
        return self._position.beats_per_bar

    @property
    def beat_type(self):
        return self._position.beat_type

    @property
    def ticks_per_beat(self):
        return self._position.ticks_per_beat

    @property
    def beats_per_minute(self):
        return self._position.beats_per_minute

    @property
    def frame_time(self):
        return self._position.frame_time

    @property
    def next_time(self):
        return self._position.next_time

    @property
    def bbt_offset(self):
        return self._position.bbt_offset

    @property
    def transport_info(self):
        """Return all transport informations

        Return a dict with following keys :
          Transport Status :
            * state : transport state : STOPPED, ROLLING, ...
          Transport position fields :
            * usecs : monotonic, free-rolling
            * frame_rate : current frame rate (per second)
            * frame : frame number (frame count since transport start)
          BBT fields :
            * bar: current bar
            * beat: current beat-within-bar
            * tick: current tick-within-beat
            * bar_start_tick : ?
            * bbt_offset : frame offset for the BBT fields (see below)
          time signature fields :
            * beats_per_bar : time signature "numerator"
            * beat_type : time signature "denominator"
            * ticks_per_beat : ticks per beat
            * beats_per_minute : current tempo (BPM)
          timecode fields :
            * frame_time : current time in seconds
            * next_time : next sequential frame_time (unless repositioned)

        About bbt_offset : frame offset for the BBT fields (the given bar,
        beat, and tick values actually refer to a time frame_offset frames
        before the start of the cycle), should be assumed to be 0 if
        JackBBTFrameOffset is not set. If JackBBTFrameOffset is set and this
        value is zero, the BBT time refers to the first frame of this cycle. If
        the value is positive, the BBT time refers to a frame that many frames
        before the start of the cycle.

        Jack video positional data are not copied to dict"""

        # Check consistency of data
        # if self._position.unique_1 == 0:
        #    raise JackError("Zero unique ID")
        if self._position.unique_1 != self._position.unique_2:
            raise JackError("Unique unique not matching : {} <> {}".
                            format(self._position.unique_1,
                                   self._position.unique_2))

        # Populate dict
        res = {}
        res['state'] = self.state
        res['usecs'] = self.usecs
        res['frame_rate'] = self.frame_rate
        res['frame'] = self.frame

        # Check if BBT fields are present
        if self.valid & self.BBT:
            res['bar'] = self.bar
            res['beat'] = self.beat
            res['tick'] = self.tick
            res['bar_start_tick'] = self.bar_start_tick
            res['beats_per_bar'] = self.beats_per_bar
            res['beat_type'] = self.beat_type
            res['ticks_per_beat'] = self.ticks_per_beat
            res['beats_per_minute'] = self.beats_per_minute

        # check if Timecode fields are present
        if self.valid & self.TIMECODE:
            res['frame_time'] = self.frame_time
            res['next_time'] = self.next_time

        # check BBT Frame offset field
        if self.valid & self.BBTFRAMEOFFSET:
            res['bbt_offset'] = self.bbt_offset

        return res
