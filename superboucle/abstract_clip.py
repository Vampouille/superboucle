class AbstractClip:
    DEFAULT_OUTPUT = "Main"

    STOP = 0
    STARTING = 1
    START = 2
    STOPPING = 3
    PREPARE_RECORD = 4
    RECORDING = 5

    TRANSITION = {STOP: STARTING,
                  STARTING: STOP,
                  START: STOPPING,
                  STOPPING: START,
                  PREPARE_RECORD: RECORDING,
                  RECORDING: PREPARE_RECORD}
    RECORD_TRANSITION = {STOP: PREPARE_RECORD,
                         PREPARE_RECORD: STOP,
                         STARTING: STOP,
                         START: STOP,
                         STOPPING: STOP,
                         RECORDING: STOP}
    STATE_DESCRIPTION = {0: "STOP",
                         1: "STARTING",
                         2: "START",
                         3: "STOPPING",
                         4: "PREPARE_RECORD",
                         5: "RECORDING"}

    def __init__(self, name='', volume=1, output=DEFAULT_OUTPUT, mute_group=0):
        self.name = name
        self.volume = volume
        self.state = AbstractClip.STOP
        self.output = output
        self.mute_group = mute_group

    def stop(self):
        self.state = AbstractClip.STOPPING if self.state == AbstractClip.START \
            else AbstractClip.STOP if self.state == AbstractClip.STARTING \
            else self.state

    def start(self):
        self.state = AbstractClip.STARTING if self.state == AbstractClip.STOP \
            else AbstractClip.START if self.state == AbstractClip.STOPPING \
            else self.state

    # To implement:
    # def rewind(self):
    # def getPos(self): # position relative to the clip between 0 and 1

