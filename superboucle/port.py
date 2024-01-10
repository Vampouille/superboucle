import re
from superboucle.jack_client import client

class AbstractPort:
    def __init__(self, type, name=None, regexp=None, json=None) -> None:
        self.type = type
        if json is not None:
            self.name = json['name']
            self.regexp = json['regexp'] if 'regexp' in json else None
        else:
            self.name = name
            self.regexp = regexp
        self.ports = client.outports if type == AudioPort else client.midi_outports if type == MidiPort else None
        if self.ports is None:
            raise Exception("This class should not be used directly")

    def serialize(self):
        res = {"name": self.name}
        if self.regexp is not None:
            res["regexp"] = self.regexp
        return res

    def findPort(self, regexp):
        return client.get_ports(name_pattern='' if regexp is None else regexp,
                                is_physical=True,
                                is_input=True,
                                is_audio=isinstance(self, AudioPort),
                                is_midi=isinstance(self, MidiPort))
    
    def _register(self, port_short_name):
        # Search if port is already registered
        for p in self.ports:
            if p.shortname == port_short_name:
                return
        self.ports.register(port_short_name)

    def unregister(self):
        for p in self.ports:
            if p.shortname in self.getShortNames():
                p.unregister()
                break

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, AbstractPort):
            return False
        return self.type == __value.type and self.name == __value.name
    
    def __hash__(self):
        return hash((self.type, self.name))

class AudioPort(AbstractPort):

    def __init__(self, name=None, regexp=None, json=None) -> None:
        super().__init__(AudioPort, name, regexp, json)

    def register(self):
        self._register("%s_L" % self.name)
        self._register("%s_R" % self.name)

    def getShortNames(self):
        return ["%s_L" % self.name, "%s_R" % self.name]

class MidiPort(AbstractPort):

    def __init__(self, name=None, regexp=None, json=None) -> None:
        super().__init__(MidiPort, name, regexp, json)

    def register(self):
        self._register(self.name)

    def getShortNames(self):
        return [self.name]