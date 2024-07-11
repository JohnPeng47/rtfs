import json
from enum import Enum

from src.scope_resolution.imports import LocalImportStmt
from src.utils import load_sys_modules


class ModuleType(str, Enum):
    # a local package
    LOCAL = "local"
    # system/core lib
    SYS = "sys"
    # third party lib
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


class ImportBlock:
    def __init__(self, import_stmt: LocalImportStmt, lang: str = "python"):
        self.sys_modules_list = load_sys_modules(lang)
        self.module_type = ModuleType.UNKNOWN

        if import_stmt.module:
            self.module = import_stmt.module
        else:
            # name is the module
            assert len(import_stmt.names) == 1
            self.module = import_stmt.names[0]

        # determine module type
        if self.module in self.sys_modules_list:
            self.module_type = ModuleType.SYS
