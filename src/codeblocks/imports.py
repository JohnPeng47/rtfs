from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from src.scope_resolution.imports import LocalImportStmt
from src.codeblocks.namespace import NameSpace
from src.fs import RepoFs
from src.utils import SysModules, ThirdPartyModules


from config import LANGUAGE


class ModuleType(str, Enum):
    # a local package
    LOCAL = "local"
    # system/core lib
    SYS = "sys"
    # third party lib
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


def import_stmt_to_import(
    import_stmt: LocalImportStmt,
    filepath: Path,
    fs: RepoFs,
    sys_modules: SysModules,
    third_party_modules: ThirdPartyModules,
) -> Dict[NameSpace, ModuleType]:
    """
    Convert an import statement, which may hold multiple imports
    """
    imports = []
    namespaces = []

    # from foo.bar import baz
    # root_ns = foo.bar
    # name = baz
    # namespaces = [foo.bar.baz]

    if import_stmt.from_name:
        root = import_stmt.from_name
        for name in import_stmt.names:
            namespaces += [NameSpace(root, child=name)]

    else:
        namespaces = [NameSpace(n) for n in import_stmt.names]

    # resolve module type
    import_path = None
    for ns in namespaces:
        if ns.root in sys_modules:
            module_type = ModuleType.SYS
        elif ns.root in third_party_modules:
            module_type = ModuleType.THIRD_PARTY
        elif import_path := fs.match_file(ns.to_path()):
            module_type = ModuleType.LOCAL
        else:
            module_type = ModuleType.UNKNOWN

        imports.append(Import(ns, module_type, filepath, import_path=import_path))
    return imports


@dataclass
class Import:
    """
    This represents a single Import that is the result of joining
    from_name and names in LocalImportStmt
    """

    namespace: NameSpace
    module_type: ModuleType
    filepath: Path
    # only for ModuleType.LOCAL
    import_path: Optional[Path] = None
