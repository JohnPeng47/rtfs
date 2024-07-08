from pydantic import BaseModel

from typing import Optional
from enum import Enum

from src.utils import TextRange


class NodeKind(str, Enum):
    SCOPE = "LocalScope"
    DEFINITION = "LocalDef"
    LOCAL_IMPORT = "LocalImport"
    REF = "Reference"


class ScopeNode(BaseModel):
    range: TextRange
    type: NodeKind
    symbol_id: Optional[str] = None


class EdgeKind(str, Enum):
    ScopeToScope = "ScopeToScope"
    DefToScope = "DefToScope"
    ImportToScope = "ImportToScope"
    RefToDef = "RefToDef"
    RefToImport = "RefToImport"
