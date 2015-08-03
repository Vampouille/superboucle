from clip import Clip
from inspect import getmembers
from midi_actions import MidiAction
import struct
import json


class DeviceOutput:
    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls=None):
        mapping = inst.output_mapping
        if self.name not in mapping:
            mapping[self.name] = self.method(inst)
        return mapping[self.name]

    def __set__(self, inst, value):
        mapping = inst.output_mapping
        mapping[self.name] = value
        inst.update_lookup()

    def __delete__(self, inst):
        mapping = inst.output_mapping
        del mapping[self.name]
        inst.update_lookup()


class Device():
    COLOR_DICT = {
        None: 'none_vel',
        Clip.STOP: 'stop_vel',
        Clip.STARTING: 'starting_vel',
        Clip.START: 'start_vel',
        Clip.STOPPING: 'stopping_vel',
        Clip.PREPARE_RECORD: 'prepare_record_vel',
        Clip.RECORDING: 'recording_vel'
    }

    def __init__(self, name=''):
        self.input_mapping = {}
        self.output_mapping = {}
        self.name = name
        # initializes all fields with defaults
        self._lookup_note = {}
        getmembers(self)
        self.update_lookup()

    def update_lookup(self):
        try:
            self._lookup_note = {tuple(m): n
                                 for n in MidiAction.ALL_INSTANCES
                                 for m in
                                 MidiAction.get(n, self).get_midi_keys()}
        except Exception as e:
            print(e)

    def get_action(self, midi_message):
        midi_key = MidiAction.make_midi_key(midi_message)
        midi_action_name = self._lookup_note[midi_key]
        return MidiAction.get(midi_action_name, self)

    def update(self, other_device):
        self.name = other_device.name
        self.input_mapping = other_device.input_mapping.copy()
        self.output_mapping = other_device.output_mapping.copy()
        self.update_lookup()

    def learn(self, midi_message):
        midi_action = MidiAction.get(MidiAction.LISTENING, self)
        if midi_action.ignore_message(midi_message):
            return
        midi_key = MidiAction.make_midi_key(midi_message)
        midi_action.teach(midi_key)
        self.update_lookup()

    @staticmethod
    def decode_midi(data):
        if len(data) == 3:
            status, pitch, vel = struct.unpack('3B', data)
            channel = status & 0xF
            msg_type = status >> 4
            return msg_type, channel, pitch, vel
        else:
            raise Exception('Invalid Midi message length')

    def generate_feedback_note(self, action, state, *args):
        midi_action = MidiAction.get(action, self)
        midi_key = midi_action.args_to_midi(*args)
        return self.encode_feedback_note(midi_key, self.get_color(state))

    def generate_feedback_notes(self, action, color):
        midi_action = MidiAction.get(action, self)
        midi_keys = midi_action.get_midi_keys()
        return [self.encode_feedback_note(key, color) for key in midi_keys]

    def encode_feedback_note(self, midi_key, velocity):
        msg_type, channel, pitch = midi_key
        return MidiAction.NOTEON << 4 | channel, pitch, velocity

    def get_color(self, state):
        if state in Device.COLOR_DICT:
            color_key = Device.COLOR_DICT[state]
            return self.output_mapping[color_key]
        else:
            raise Exception("Invalid state")

    def toJson(self):
        return json.dumps({
            'name': self.name,
            'input_mapping': self.input_mapping,
            'output_mapping': self.output_mapping
        })

    @staticmethod
    def fromJson(json_data):
        data = json.loads(json_data)
        d = Device(data['name'])
        d.input_mapping = data['input_mapping']
        d.output_mapping = data['output_mapping']
        d.update_lookup()
        return d

    # outputs
    @DeviceOutput
    def init_command(self):
        return []

    # velocity feedback
    @DeviceOutput
    def none_vel(self):
        return 0

    @DeviceOutput
    def start_vel(self):
        return 0

    @DeviceOutput
    def starting_vel(self):
        return 0

    @DeviceOutput
    def stop_vel(self):
        return 0

    @DeviceOutput
    def stopping_vel(self):
        return 0

    @DeviceOutput
    def recording_vel(self):
        return 0

    @DeviceOutput
    def prepare_record_vel(self):
        return 0
