import json
from enum import Enum
from typing import Dict

from src.scope_resolution.imports import LocalImportStmt
from src.utils import load_sys_modules
from src.codeblocks.namespace import NameSpace
from src.fs import RepoFs

from config import LANGUAGE


class ModuleType(str, Enum):
    # a local package
    LOCAL = "local"
    # system/core lib
    SYS = "sys"
    # third party lib
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


# TODO: this lang parameter needs to go
class ImportBlock:
    def __init__(self, import_stmt: LocalImportStmt, fs: RepoFs):
        self.namespaces: Dict[NameSpace, ModuleType] = {}
        self.module_type = ModuleType.UNKNOWN

        # resolve namespaces
        namespaces = []
        if import_stmt.from_name:
            namespaces += [NameSpace(import_stmt.from_name)]
        else:
            namespaces = [NameSpace(n) for n in import_stmt.names]

        # resolve module type
        for ns in namespaces:
            if ns.root in load_sys_modules(LANGUAGE):
                self.module_type = ModuleType.SYS
            else:
                self.module_type = ModuleType.LOCAL

            self.namespaces[ns] = self.module_type
