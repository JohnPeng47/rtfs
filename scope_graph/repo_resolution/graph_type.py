from scope_graph.scope_resolution.graph import ScopeID, Node
from enum import Enum

from pathlib import Path


class RepoNode(Node):
    id: str
    name: str

    def __str__(self):
        return f"{self.name}"


class EdgeKind(str, Enum):
    ImportToExport = "ImportToExport"
