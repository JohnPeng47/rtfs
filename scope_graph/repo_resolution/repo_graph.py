from typing import Any, List, Dict
from pathlib import Path

from scope_graph.fs import RepoFs
from scope_graph.build_scopes import ScopeGraph, build_scope_graph
from scope_graph.scope_resolution import LocalImportStmt
from scope_graph.utils import SysModules, ThirdPartyModules
from scope_graph.codeblocks.imports import Import, import_stmt_to_import
from scope_graph.config import LANGUAGE


# rename to import graph?
class RepoGraph:
    """
    Constructs a graph of the entire repository
    """

    def __init__(self, path: Path):
        fs = RepoFs(path)
        self.scopes_map: Dict[Path, ScopeGraph] = self.construct_scopes(fs)

        # construct file level "connection sites" for building edges
        self.imports: Dict[Path, List[Import]] = self.construct_imports(
            self.scopes_map, fs
        )

        # parse calls and parameters here
        # self.calls = self.construct_calls(self.scopes_map, fs)

        # map the chunks from Moatless
        # self.scope_chunk_map: Dict[ScopeList, Chunk]

    # TODO: add some sort of hierarchal structure to the scopes?
    def construct_scopes(self, fs: RepoFs) -> Dict[Path, ScopeGraph]:
        """
        Returns all the scopes associated with the files in the directory
        """
        scope_map = {}
        for path, file_content in fs.get_files_content():
            scope_map[path] = build_scope_graph(file_content, language=LANGUAGE)

        return scope_map

    # ultimately the output should be 3-tuple
    # (import_stmt, path, import_type)
    def construct_imports(
        self, scopes: Dict[Path, ScopeGraph], fs: RepoFs
    ) -> Dict[Path, List[Import]]:
        """
        Constructs a map from file to its imports
        """
        # lists for checking if python module is system or third party
        sys_modules_list = SysModules(LANGUAGE)
        third_party_modules_list = ThirdPartyModules(LANGUAGE)

        import_map = {}

        for file, scope_graph in scopes.items():
            imports = self.get_imports(
                scope_graph, file, fs, sys_modules_list, third_party_modules_list
            )
            import_map[file] = imports

        return import_map

    def get_imports(
        self,
        g: ScopeGraph,
        file: Path,
        fs: RepoFs,
        sys_modules: SysModules,
        third_party_modules: ThirdPartyModules,
    ) -> List[Import]:
        """
        Get all imports from a ScopeGraph
        """
        imports = []

        for scope in g.scopes():
            for imp in g.imports(scope):
                imp_node = g.get_node(imp)
                imp_stmt = LocalImportStmt(imp_node.range, **imp_node.data)
                imp_blocks = import_stmt_to_import(
                    import_stmt=imp_stmt,
                    filepath=file,
                    fs=fs,
                    sys_modules=sys_modules,
                    third_party_modules=third_party_modules,
                )

                imports.extend(imp_blocks)

        return imports
