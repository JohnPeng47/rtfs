from config import NAMESPACE_DELIMETERS, LANGUAGE

delimiter = NAMESPACE_DELIMETERS[LANGUAGE]


class NameSpace:
    def __init__(self, name: str):
        self.namespace = name.split(delimiter)

    @property
    def root(self):
        return self.namespace[0]

    def __hash__(self):
        return hash(tuple(self.namespace))
