from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from scope_graph.build_scopes import ScopeGraph
from scope_graph.scope_resolution.imports import LocalImportStmt
from scope_graph.codeblocks.namespace import NameSpace
from scope_graph.fs import RepoFs
from scope_graph.utils import SysModules, ThirdPartyModules


class ModuleType(str, Enum):
    # a local package
    LOCAL = "local"
    # system/core lib
    SYS = "sys"
    # third party lib
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


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
    # if this import is defined in a scope
    def_scope: Optional[int] = None


def import_stmt_to_import(
    import_stmt: LocalImportStmt,
    filepath: Path,
    scope_graph: ScopeGraph,
    fs: RepoFs,
    sys_modules: SysModules,
    third_party_modules: ThirdPartyModules,
) -> List[Import]:
    """
    Convert an import statement, which may hold multiple imports
    """
    imports = []
    namespaces = []

    print("FILEPAHT: ", filepath)
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

        # try to match import with scope of def
        defscope_id = None
        for scope in scope_graph.scopes():
            for definition in scope_graph.definitions(scope):
                def_node = scope_graph.get_node(definition)
                if def_node.name == ns.child:
                    defscope_id = scope
                    print(f"Found import in scope: {ns.root} {defscope_id}")
                    break

        imports.append(
            Import(
                ns,
                module_type,
                filepath,
                import_path=import_path,
                def_scope=defscope_id,
            )
        )

    return imports
