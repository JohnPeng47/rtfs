from enum import Enum
from typing import NewType
import os
from dataclasses import dataclass

from rtfs.scope_resolution.scope_graph import ScopeID
from rtfs.graph import Node, Edge

RepoNodeID = NewType("RepoNodeID", str)


@dataclass(kw_only=True)
class RepoNode(Node):
    kind: str = "RepoNode"
    file_path: str = None
    scope: ScopeID = None

    @property
    def name(self):
        return f"{os.path.basename(self.file_path)}::{self.scope}"

    def __str__(self):
        return f"{self.name}"


class EdgeKind(str, Enum):
    ImportToExport = "ImportToExport"


@dataclass(kw_only=True)
class RefEdge(Edge):
    type: EdgeKind = EdgeKind.ImportToExport
    ref: str
    defn: str
