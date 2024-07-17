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

from .imports import Import, import_stmt_to_import
from .exports import Export
from .graph_type import RepoNode

import logging

logger = logging.getLogger(__name__)


# rename to import graph?
# probably not, since we do want struct to hold repo level info
class RepoGraph:
    """
    Constructs a graph of relation between files in a repo
    """

    def __init__(self, path: Path):
        fs = RepoFs(path)

        self._graph = DiGraph()

        self.scopes_map: Dict[Path, ScopeGraph] = self.construct_scopes(fs)

        self._imports: Dict[Path, List[Import]] = {}
        self._exports: Dict[Path, List[Export]] = {}

        # construct exports
        for path, g in self.scopes_map.items():
            self._exports[path] = self.construct_exports(g, path)

        # construct imports
        for path, g in self.scopes_map.items():
            self._imports = self.construct_import(g, path, fs)

        # parse calls and parameters here
        # self.calls = self.construct_calls(self.scopes_map, fs)

        # map the chunks from Moatless
        # self.scope_chunk_map: Dict[ScopeList, Chunk]

    def create_node(self, node: RepoNode):
        self._graph.add_node(**node.dict())

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
    def construct_exports(self, g: ScopeGraph, file: Path) -> List[Export]:
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
                    logger.debug("File export: ", file, "DEF_NODE: ", def_node.name)
                    exports.append(Export(def_node.name, scope, file))

        return exports
