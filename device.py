from clip import Clip


class Device():

    NOTEON = 0x90
    NOTEOFF = 0x80

    def __init__(self, mapping=None):
        self.note_to_coord = {}
        if mapping is None:
            self.mapping = {}
        else:
            self.mapping = mapping
        for x in range(len(self.start_stop)):
            line = self.start_stop[x]
            for y in range(len(line)):
                line[y] = tuple(line[y])
                self.note_to_coord[line[y]] = (x, y)
        for x in range(len(self.block_buttons)):
            self.block_buttons[x] = tuple(self.block_buttons[x])
        for x in range(len(self.ctrls)):
            self.ctrls[x] = tuple(self.ctrls[x])

    def generateNote(self, x, y, state):
        # print("Generate note for cell {0} {1} and state {2}".
        #      format(x, y, state))
        (msg_type, channel, pitch, velocity) = self.start_stop[x][y]
        return (self.NOTEON + channel, pitch, self.get_color(state))

#    def __str__(self):
#        return str(self.mapping)

    def get_color(self, state):
        if state == Clip.STOP:
            return self.red_vel
        elif state == Clip.STARTING:
            return self.blink_green_vel
        elif state == Clip.START:
            return self.green_vel
        elif state == Clip.STOPPING:
            return self.blink_red_vel
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
