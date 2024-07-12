from typing import Any, List, Dict
from pathlib import Path

from src.fs import RepoFs
from src.build_scopes import ScopeGraph, build_scope_graph
from src.scope_resolution import LocalImportStmt
from src.codeblocks.imports import ImportBlock
from config import LANGUAGE


class RepoGraph:
    """
    Constructs a graph of the entire repository
    """

    def __init__(self, path: Path):
        fs = RepoFs(path)
        self.scopes_map: Dict[Path, ScopeGraph] = self.construct_scopes(fs)

        # construct file level "connection sites" for building edges
        self.imports: Dict[Path, List[ImportBlock]] = self.construct_imports(
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
        for file in fs.get_files_content():
            scope_map[file] = build_scope_graph(file, language=LANGUAGE)

        return scope_map

    def construct_imports(
        self, scopes: Dict[Path, ScopeGraph], fs: RepoFs
    ) -> Dict[Path, List[ImportBlock]]:
        """
        Constructs a map from file to its imports
        """
        import_map = {}
        for file, scope_graph in scopes.items():
            imports = self.get_imports(scope_graph, file, fs)
            import_map[file] = imports

        return import_map

    def get_imports(self, g: ScopeGraph, file: Path, fs: RepoFs) -> List[ImportBlock]:
        """
        Get all imports from a ScopeGraph
        """
        imports = []
        for scope in g.scopes():
            for imp in g.imports(scope):
                imp_node = g.get_node(imp)
                imp_stmt = LocalImportStmt(imp_node.range, **imp_node.data)

                print(imp_stmt)
                imp_block = ImportBlock(imp_stmt, fs)

                imports.append(imp_block)

        return imports

    def get_import_root(self):
        pass
