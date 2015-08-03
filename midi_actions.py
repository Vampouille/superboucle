import re
from wrapt import FunctionWrapper, decorator
from inspect import getargspec
from copy import deepcopy


@decorator
def handler(wrapped, instance, args, kwargs):
    midi_action_name = args[0]
    device = args[1]
    cb = kwargs.pop('callback', lambda: None)

    def handle():
        midi_action = MidiAction.get(midi_action_name, device)
        r = wrapped(midi_action, *args[2:], **kwargs)
        cb()
        return r

    return handle


class MidiAction(FunctionWrapper):
    NOTEON = 0x9
    NOTEOFF = 0x8
    MIDICTRL = 11

    ALL_INSTANCES = {}
    LISTENING = None

    DEFAULT_DATA = None

    _name_pattern = re.compile("^(?:on_)?(.*)$")

    @handler
    @staticmethod
    def listener(midi_action):
        MidiAction.LISTENING = midi_action._self_name
        midi_action.listen()

    @handler
    @staticmethod
    def clearer(midi_action):
        try:
            midi_action.clear()
        except KeyError:
            print('already cleared')

    @staticmethod
    def get(name, device):
        try:
            midi_action = MidiAction.ALL_INSTANCES[name]
            midi_action._self_device = device
            return midi_action
        except AttributeError:
            raise Exception('unknown midi action: '.format(name))

    @staticmethod
    def make_midi_key(midi_message):
        return midi_message[:-1]  # velocity is cut off

    """
    A Decorator for methods.

    If a Method is a MidiAction, it will be learnable and can be learned
    in devices.
    """

    def __init__(self, wrapped, name=None):
        super(MidiAction, self).__init__(wrapped, self.wrapper)
        self._self_name = name or wrapped.__name__
        self._self_device = None
        self._self_accept_vel_zero = False
        self._self_last_instance = None
        self._self_name = self._name_pattern.match(self._self_name).group(1)
        if self._self_name in self.ALL_INSTANCES:
            raise Exception('Midi action named {} already exists.'
                            .format(self._self_name))
        self.ALL_INSTANCES[self._self_name] = self

    @property
    def listening(self):
        return self.LISTENING == self._self_name

    @property
    def data(self):
        mapping = self._self_device.input_mapping
        return mapping.setdefault(self._self_name, deepcopy(self.DEFAULT_DATA))

    @data.setter
    def data(self, value):
        self._self_device.input_mapping[self._self_name] = value

    @data.deleter
    def data(self):
        del self._self_device.input_mapping[self._self_name]

    @classmethod
    def continuous(cls, method):
        ma = cls(method)
        ma._self_accept_vel_zero = True
        return ma

    def __get__(self, instance, owner):
        self._self_last_instance = instance
        return super(FunctionWrapper, self).__get__(instance, owner)

    def wrapper(self, wrapped, instance, args, kwargs):
        spec = getargspec(wrapped)
        if not spec.varargs:
            maxArgs = len(spec.args) - int(bool(instance))
            args = args[:maxArgs]
        return wrapped(*args, **kwargs)

    def ignore_message(self, midi_message):
        return not self._self_accept_vel_zero and midi_message[-1] == 0

    def trigger(self, midi_message):
        instance = self._self_last_instance
        args = self.midi_to_args(midi_message)
        function = self.__wrapped__.__get__(instance)
        return self.wrapper(function, instance, args, {})

    def midi_to_args(self, midi_message):
        return midi_message[-1:]

    def args_to_midi(self, *args):
        return self.data

    def listen(self):
        pass

    def teach(self, midi_key):
        print('learning ' + self._self_name)
        self.data = midi_key
        self.LISTENING = None

    def get_midi_keys(self):
        return [self.data] if self.data else []

    def clear(self):
        del self.data
        if self.listening:
            self.listen()


class MidiRowAction(MidiAction):
    DEFAULT_DATA = []

    def get_midi_keys(self):
        return self.data

    def _dont_learn(self, midi_key):
        already_learned = self.get_midi_keys()
        if midi_key in already_learned:
            return True
        off_key = (self.NOTEON,) + midi_key[1:]
        return midi_key[0] == self.NOTEOFF and off_key in already_learned

    def teach(self, midi_key):
        if self._dont_learn(midi_key):
            return
        print('learning ' + self._self_name)
        self.data.append(tuple(midi_key))

    def midi_to_args(self, midi_message):
        midi_key = self.make_midi_key(midi_message)
        return self.data.index(midi_key), midi_message[-1]

    def args_to_midi(self, *args):
        return self.data[args[0]]


class MidiGridAction(MidiRowAction):
    def __init__(self, wrapped, name=None):
        super(MidiGridAction, self).__init__(wrapped, name)
        self._self_current_row = None
        self.reset()

    def reset(self):
        self._self_current_row = -1

    def listen(self):
        self._self_current_row += 1
        super(MidiGridAction, self).listen()
        if (self._self_current_row == len(self.data)):
            self.data.append([])
            # data[self._self_current_row]

    def clear(self):
        self.reset()
        super(MidiGridAction, self).clear()

    def get_midi_keys(self):
        return [k for row in self.data for k in row]

    def teach(self, midi_key):
        if self._dont_learn(midi_key):
            return
        print('learning ' + self._self_name)
        self.data[self._self_current_row].append(tuple(midi_key))

    def midi_to_args(self, midi_message):
        midi_key = self.make_midi_key(midi_message)
        for y, row in enumerate(self.data):
            try:
                row_tuples = list(map(tuple, row))
                return row_tuples.index(midi_key), y, midi_message[-1]
            except ValueError:
                continue

    def args_to_midi(self, *args):
        return self.data[args[1]][args[0]]
