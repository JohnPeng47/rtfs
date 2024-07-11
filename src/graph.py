from pydantic import BaseModel

from typing import Optional, Dict
from enum import Enum

from src.utils import TextRange


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
    RefToImport = "RefToImport"
