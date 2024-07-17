from typing import Any, List, Dict, Tuple
from pathlib import Path
from collections import defaultdict
from networkx import DiGraph

from scope_graph.fs import RepoFs
from scope_graph.scope_resolution.graph import ScopeGraph, ScopeID
from scope_graph.build_scopes import build_scope_graph
from scope_graph.scope_resolution import LocalImportStmt
from scope_graph.utils import SysModules, ThirdPartyModules, TextRange
from scope_graph.config import LANGUAGE

from .imports import Import, ModuleType, import_stmt_to_import
from .graph_type import EdgeKind, RepoNode

import logging

logger = logging.getLogger(__name__)


# rename to import graph?
# probably not, since we do want struct to hold repo level info
class RepoGraph:
    """
    Constructs a graph of relation between the scopes of a repo
    """

    def __init__(self, path: Path):
        fs = RepoFs(path)

        self._graph = DiGraph()
        self.scopes_map: Dict[Path, ScopeGraph] = self.construct_scopes(fs)
        self._imports: Dict[Path, List[Import]] = {}

        # parse calls and parameters here
        # self.calls = self.construct_calls(self.scopes_map, fs)

        # construct imports
        for path, g in self.scopes_map.items():
            self._imports[path] = self.construct_import(g, path, fs)

        # map import ref to export scope
        for path, imports in self._imports.items():
            for imp in filter(lambda i: i.module_type == ModuleType.LOCAL, imports):
                local_path = fs.match_file(imp.namespace.to_path())
                if local_path:
                    for name, def_scope in self.get_exports(
                        self.scopes_map[local_path], local_path
                    ):
                        if imp.namespace.child == name:
                            for ref_scope in imp.ref_scopes:
                                # create nodes and edges
                                ref_node = self.get_node(path, ref_scope)
                                if not ref_node:
                                    ref_node = self.create_node(path, ref_scope)

                                imp_node = self.get_node(local_path, def_scope)
                                if not imp_node:
                                    imp_node = self.create_node(local_path, def_scope)

                                self._graph.add_edge(
                                    ref_node, imp_node, kind=EdgeKind.ImportToExport
                                )

    def get_node(self, file: Path, scope_id: ScopeID):
        return self._graph.nodes.get(RepoNode(str(file), scope_id), None)

    def create_node(self, file: Path, scope_id: ScopeID):
        node = RepoNode(str(file), scope_id, name=file.name)
        self._graph.add_node(node)

        return node

    # def get_node(self, file: Path, scope_id: ScopeID):
    #     return self._graph.nodes[RepoNode(file, scope_id)]

    # TODO: add some sort of hierarchal structure to the scopes?
    def construct_scopes(self, fs: RepoFs) -> Dict[Path, ScopeGraph]:
        """
        Returns all the scopes associated with the files in the directory
        """
        scope_map = {}
        for path, file_content in fs.get_files_content():
            # index by full path
            scope_map[path.resolve()] = build_scope_graph(
                file_content, language=LANGUAGE
            )

        return scope_map

    # ultimately the output should be 3-tuple
    # (import_stmt, path, import_type)
    def construct_import(
        self, g: ScopeGraph, file: Path, fs: RepoFs
    ) -> Dict[Path, List[Import]]:
        """
        Constructs a map from file to its imports
        """
        # lists for checking if python module is system or third party
        sys_modules_list = SysModules(LANGUAGE)
        third_party_modules_list = ThirdPartyModules(LANGUAGE)

        imports = []
        for imp_node in g.get_all_imports():
            imp_stmt = LocalImportStmt(imp_node.range, **imp_node.data)
            imp_blocks = import_stmt_to_import(
                import_stmt=imp_stmt,
                filepath=file,
                g=g,
                fs=fs,
                sys_modules=sys_modules_list,
                third_party_modules=third_party_modules_list,
            )
            imports.extend(imp_blocks)

        return imports

    # NOTE: this would need to be handled differently for other langs
    def get_exports(self, g: ScopeGraph, file: Path) -> List[Tuple[str, ScopeID]]:
        """
        Constructs a map from file to its exports (unreferenced definitions)
        """
        exports = []

        # have to do this because class/func defs are tied to the same scope
        # they open, so they are child of root instead of being defined at root
        outer_scopes = [g.root_idx] + [s for s in g.child_scopes(g.root_idx)]

        for scope in outer_scopes:
            for defn in g.definitions(scope):
                def_node = g.get_node(defn)
                # dont want to pick up non class/func defs in the root - 1 scope
                if scope != g.root_idx and (
                    def_node.data["def_type"] == "class"
                    or def_node.data["def_type"] == "function"
                ):
                    exports.append((def_node.name, scope))

        return exports
