from scope_graph.scope_resolution.graph import ScopeID
from enum import Enum

from pathlib import Path


class RepoNode:
    def __init__(self, path: str, scope_id: ScopeID, name: str = ""):
        self.path = path
        self.scope_id = scope_id
        self.name = name

    def __hash__(self):
        return hash(self.path + str(self.scope_id))

    def __str__(self):
        return f"{self.name}::{self.scope_id}"


class EdgeKind(str, Enum):
    ImportToExport = "ImportToExport"
