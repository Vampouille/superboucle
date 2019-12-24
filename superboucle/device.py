from superboucle.clip import Clip


class DeviceOutput:
    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def get_mapping(self, inst):
        return inst.mapping

    def __get__(self, inst, cls=None):
        mapping = self.get_mapping(inst)
        return mapping.setdefault(self.name, self.method(inst))

    def __set__(self, inst, value):
        mapping = self.get_mapping(inst)
        mapping[self.name] = value
        # inst.update_lookup()

    def __delete__(self, inst):
        mapping = self.get_mapping(inst)
        del mapping[self.name]
        # inst.update_lookup()


class DeviceInput(DeviceOutput):
    # def get_mapping(self, inst):
    #    return inst.mapping

    pass


class Device:
    def __init__(self, mapping={}):
        self.updateMapping(mapping)

    def updateMapping(self, new_mapping):
        self.note_to_coord = {}
        for key in new_mapping.keys():
            new_mapping[key] = self._formatMapping(new_mapping[key])
        self.mapping = new_mapping
        for y in range(len(self.start_stop)):
            line = self.start_stop[y]
            for x in range(len(line)):
                self.note_to_coord[line[x]] = (x, y)

    def _formatMapping(self, value):
        if type(value) is not list or not len(value):
            return value
        elif type(value[0]) is int:
            return tuple(value)
        elif type(value[0]) is list:
            return [self._formatMapping(v) for v in value]
        else:
            print("Unknown structure...")
            return value

    def generateNote(self, x, y, state):
        (msg_type, channel, pitch, velocity) = self.start_stop[y][x]
        return (0x90 + channel, pitch, self.getColor(state))  # note on : 0x90

    def getColor(self, state):
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
        return self.mapping.get('name', '')

    @name.setter
    def name(self, name):
        self.mapping['name'] = name

    @DeviceInput
    def ctrls(self):
        return []

    @DeviceInput
    def start_stop(self):
        return []

    @DeviceInput
    def init_command(self):
        return []

    @DeviceInput
    def block_buttons(self):
        return []

    @DeviceInput
    def scene_buttons(self):
        return []

    @DeviceInput
    def master_volume_ctrl(self):
        return False

    @DeviceInput
    def play_btn(self):
        return False

    @DeviceInput
    def pause_btn(self):
        return False

    @DeviceInput
    def rewind_btn(self):
        return False

    @DeviceInput
    def goto_btn(self):
        return False

    @DeviceInput
    def record_btn(self):
        return False

    @DeviceOutput
    def black_vel(self):
        return 0

    @DeviceOutput
    def green_vel(self):
        return 0

    @DeviceOutput
    def blink_green_vel(self):
        return 0

    @DeviceOutput
    def red_vel(self):
        return 0

    @DeviceOutput
    def blink_red_vel(self):
        return 0

    @DeviceOutput
    def amber_vel(self):
        return 0

    @DeviceOutput
    def blink_amber_vel(self):
        return 0
