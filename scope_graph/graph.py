from pydantic import BaseModel

from typing import Optional, Dict, NewType
from enum import Enum

from scope_graph.utils import TextRange


class NodeKind(str, Enum):
    SCOPE = "LocalScope"
    DEFINITION = "LocalDef"
    IMPORT = "Import"
    REFERENCE = "Reference"


class ScopeNode(BaseModel):
    range: TextRange
    type: NodeKind
    def_type: Optional[str] = ""
    name: Optional[str] = ""
    data: Optional[Dict] = {}


class EdgeKind(str, Enum):
    ScopeToScope = "ScopeToScope"
    DefToScope = "DefToScope"
    ImportToScope = "ImportToScope"
    RefToDef = "RefToDef"
    RefToOrigin = "RefToOrigin"
    RefToImport = "RefToImport"
