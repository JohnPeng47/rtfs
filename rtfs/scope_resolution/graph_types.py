from typing import Dict, Optional, NewType
from enum import Enum
from pydantic import root_validator

from rtfs.graph import Node
from rtfs.utils import TextRange
import random
import string


class NodeKind(str, Enum):
    SCOPE = "LocalScope"
    DEFINITION = "LocalDef"
    IMPORT = "Import"
    REFERENCE = "Reference"
    CALL = "Call"


class EdgeKind(str, Enum):
    ScopeToScope = "ScopeToScope"
    DefToScope = "DefToScope"
    ImportToScope = "ImportToScope"
    RefToDef = "RefToDef"
    RefToOrigin = "RefToOrigin"
    RefToImport = "RefToImport"
    CallToRef = "CallToRef"


class ScopeNode(Node):
    # jank..
    id: str = "".join(random.choices(string.ascii_letters, k=6))
    range: TextRange
    type: NodeKind
    name: Optional[str] = ""
    data: Optional[Dict] = {}


ScopeID = NewType("ScopeID", int)
