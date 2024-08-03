from rtfs.scope_resolution.graph import ScopeID
from rtfs.graph import Node, Edge
from enum import Enum
from typing import NewType
import os

from pydantic import root_validator


RepoNodeID = NewType("RepoNodeID", str)


class RepoNodeType(str, Enum):
    Ref = "Ref"
    Def = "Def"


class RepoNode(Node):
    id: RepoNodeID
    name: str = None
    file_path: str = None
    scope: ScopeID = None

    @root_validator(pre=True)
    def validate_id(cls, values):
        repo_id = values.get("id")
        parts = repo_id.split("::")

        if len(parts) != 2:
            raise ValueError(f"Invalid repo_id format: {repo_id}")

        filepath = parts[0]
        name = filepath.split(os.sep)[-1]

        values["name"] = name
        values["file_path"] = filepath
        values["scope"] = ScopeID(parts[1])
        return values

    def __str__(self):
        return f"{self.name}::{self.scope}"


class EdgeKind(str, Enum):
    ImportToExport = "ImportToExport"


class RepoEdge(Edge):
    type: EdgeKind


class RefEdge(RepoEdge):
    type: EdgeKind = EdgeKind.ImportToExport
    ref: str
    defn: str
