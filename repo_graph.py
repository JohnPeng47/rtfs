from typing import Any, List

from src.build_scopes import ScopeGraph


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
