from scope_graph.scope_resolution.graph import ScopeID
from scope_graph.graph import Node
from enum import Enum

from pathlib import Path


class RepoNode(Node):
    def __init__(self, path: Path, scope_id: ScopeID):
        self.path = str(path)
        self.scope_id = scope_id

    def __hash__(self):
        return hash(self.path + self.scope_id)

    # def __eq__(self, other):
    #     return self.__hash__() == other.__hash__()


class EdgeKind(str, Enum):
    ImportToExport = "ScopeToScope"
