from clip import Clip


class Device():

    def __init__(self, mapping=None):
        if mapping is None:
            self.updateMapping({})
        else:
            self.updateMapping(mapping)

    def updateMapping(self, new_mapping):
        self.note_to_coord = {}
        self.mapping = new_mapping
        for y in range(len(self.start_stop)):
            line = self.start_stop[y]
            for x in range(len(line)):
                self.note_to_coord[line[x]] = (x, y)

    def generateNote(self, x, y, state):
        (msg_type, channel, pitch, velocity) = self.start_stop[y][x]
        return (0x90 + channel, pitch, self.get_color(state))  # note on : 0x90

    def get_color(self, state):
        if state is None:
            return self.black_vel
        elif state == Clip.STOP:
            return self.red_vel
        elif state == Clip.STARTING:
            return self.blink_green_vel
        elif state == Clip.START:
            return self.green_vel
        elif state == Clip.STOPPING:
            return self.blink_red_vel
        elif state == Clip.PREPARE_RECORD:
            return self.blink_amber_vel
        elif state == Clip.RECORDING:
            return self.amber_vel
        else:
            raise Exception("Invalid state")

    def getXY(self, note):
        return self.note_to_coord[note]

    @property
    def name(self):
        if 'name' in self.mapping:
            return self.mapping['name']
        else:
            return ""

    @name.setter
    def name(self, name):
        self.mapping['name'] = name

    @property
    def ctrls(self):
        if 'ctrls' not in self.mapping:
            self.mapping['ctrls'] = []
        return self.mapping['ctrls']

    @property
    def start_stop(self):
        if 'start_stop' not in self.mapping:
            self.mapping['start_stop'] = []
        return self.mapping['start_stop']

    @property
    def init_command(self):
        if 'init_command' not in self.mapping:
            self.mapping['init_command'] = []
        return self.mapping['init_command']

    @property
    def block_buttons(self):
        if 'block_buttons' not in self.mapping:
            self.mapping['block_buttons'] = []
        return self.mapping['block_buttons']

    @property
    def master_volume_ctrl(self):
        if 'master_volume_ctrl' in self.mapping:
            return self.mapping['master_volume_ctrl']
        else:
            return False

    @master_volume_ctrl.setter
    def master_volume_ctrl(self, ctrl_key):
        self.mapping['master_volume_ctrl'] = ctrl_key

    @property
    def play_btn(self):
        if 'play_btn' in self.mapping:
            return self.mapping['play_btn']
        else:
            return False

    @play_btn.setter
    def play_btn(self, btn):
        self.mapping['play_btn'] = btn

    @property
    def pause_btn(self):
        if 'pause_btn' in self.mapping:
            return self.mapping['pause_btn']
        else:
            return False

    @pause_btn.setter
    def pause_btn(self, btn):
        self.mapping['pause_btn'] = btn

    @property
    def rewind_btn(self):
        if 'rewind_btn' in self.mapping:
            return self.mapping['rewind_btn']
        else:
            return False

    @rewind_btn.setter
    def rewind_btn(self, btn):
        self.mapping['rewind_btn'] = btn

    @property
    def goto_btn(self):
        if 'goto_btn' in self.mapping:
            return self.mapping['goto_btn']
        else:
            return False

    @goto_btn.setter
    def goto_btn(self, btn):
        self.mapping['goto_btn'] = btn

    @property
    def record_btn(self):
        if 'record_btn' in self.mapping:
            return self.mapping['record_btn']
        else:
            return False

    @record_btn.setter
    def record_btn(self, btn):
        self.mapping['record_btn'] = btn

    @master_volume_ctrl.setter
    def master_volume_ctrl(self, ctrl_key):
        self.mapping['master_volume_ctrl'] = ctrl_key

    @property
    def black_vel(self):
        if 'black_vel' in self.mapping:
            return self.mapping['black_vel']
        else:
            return 0

    @property
    def green_vel(self):
        if 'green_vel' in self.mapping:
            return self.mapping['green_vel']
        else:
            return 0

    @property
    def blink_green_vel(self):
        if 'blink_green_vel' in self.mapping:
            return self.mapping['blink_green_vel']
        else:
            return 0

    @property
    def red_vel(self):
        if 'red_vel' in self.mapping:
            return self.mapping['red_vel']
        else:
            return 0

    @property
    def blink_red_vel(self):
        if 'blink_red_vel' in self.mapping:
            return self.mapping['blink_red_vel']
        else:
            return 0

    @property
    def amber_vel(self):
        if 'amber_vel' in self.mapping:
            return self.mapping['amber_vel']
        else:
            return 0

    @property
    def blink_amber_vel(self):
        if 'blink_amber_vel' in self.mapping:
            return self.mapping['blink_amber_vel']
        else:
            return 0

    @black_vel.setter
    def black_vel(self, vel):
        self.mapping['black_vel'] = vel

    @green_vel.setter
    def green_vel(self, vel):
        self.mapping['green_vel'] = vel

    @blink_green_vel.setter
    def blink_green_vel(self, vel):
        self.mapping['blink_green_vel'] = vel

    @red_vel.setter
    def red_vel(self, vel):
        self.mapping['red_vel'] = vel

    @blink_red_vel.setter
    def blink_red_vel(self, vel):
        self.mapping['blink_red_vel'] = vel

    @amber_vel.setter
    def amber_vel(self, vel):
        self.mapping['amber_vel'] = vel

    @blink_amber_vel.setter
    def blink_amber_vel(self, vel):
        self.mapping['blink_amber_vel'] = vel
