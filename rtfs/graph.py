from dataclasses import dataclass

class DictMixin:
    def dict(self):
        return self.__dict__

@dataclass
class Node(DictMixin):
    pass


@dataclass
class Edge(DictMixin):
    pass
