from typing import Any, List
from pathlib import Path

from src.build_scopes import ScopeGraph, build_scope_graph
from src.scope_resolution import LocalImportStmt
from src.codeblocks import ImportBlock


class Module:
    exports: List[str]
    imports: List[str]

    def __init__(self, graph: ScopeGraph):
        self.exports = self.get_exports(graph)

    def get_exports(self, graph: ScopeGraph) -> List[str]:
        exports = []

        # get definitions in root scope
        for def_statmt in graph.definitions(graph.root_idx):
            def_node = graph.get_node(def_statmt)
            exports.append(def_node.name)

        # basically just get all function and classes defined in root;
        # caveat is, definitions are defined at scope lvl, and since they
        # each open a new scope, we have to look for their definitions 1 away from root
        outer_scopes = graph.child_scopes(graph.root_idx)
        for scope in outer_scopes:
            defs = graph.definitions(scope)
            for d in defs:
                def_node = graph.get_node(d)
                if (
                    def_node.def_type
                    and def_node.def_type == "function"
                    or def_node.def_type == "class"
                ):
                    exports.append(def_node.name)
                    continue

        return exports

    def get_imports(self):
        pass


class RepoGraph:
    """
    Constructs a graph of the entire repository
    """

    def __init__(self, path: Path, lang: str = "python"):
        self.lang = lang
        self.scopes = []
        for file in path.rglob("*.py"):
            g = build_scope_graph(file.read_bytes(), language=lang)
            imports = self.get_imports(g)
            print("Imports for file: ", str(file))
            for imp in imports:
                print(imp.module)
            # for imp in imports:
            #     print(imp)

    def get_imports(self, g: ScopeGraph) -> List[ImportBlock]:
        """
        Get all imports from a ScopeGraph
        """
        imports = []
        for scope in g.scopes():
            for imp in g.imports(scope):
                imp_node = g.get_node(imp)
                imp_stmt = LocalImportStmt(imp_node.range, **imp_node.data)
                imp_block = ImportBlock(imp_stmt, lang=self.lang)

                imports.append(imp_block)

        return imports

    def get_import_root(self):
        pass


RepoGraph(Path("tests/repos/codecov-cli-neuteured/codecov_cli/plugins"))
