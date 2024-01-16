import re


class AbstractPort:
    def __init__(self, type, name=None, regexp=None, json=None) -> None:
        self.type = type
        if json is not None:
            self.name = json['name']
            self.regexp = json['regexp'] if 'regexp' in json else None
        else:
            self.name = name
            self.regexp = regexp

    def serialize(self):
        res = {"name": self.name}
        if self.regexp is not None:
            res["regexp"] = self.regexp
        return res

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, AbstractPort):
            return False
        return self.type == __value.type and self.name == __value.name
    
    def __hash__(self):
        return hash((self.type, self.name))

class AudioPort(AbstractPort):

    def __init__(self, name=None, regexp=None, json=None) -> None:
        super().__init__(AudioPort, name, regexp, json)

    def getShortNames(self):
        return ["%s_L" % self.name, "%s_R" % self.name]

class MidiPort(AbstractPort):

    def __init__(self, name=None, regexp=None, json=None) -> None:
        super().__init__(MidiPort, name, regexp, json)

    def getShortNames(self):
        return [self.name]