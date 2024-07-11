from typing import Any, List, Dict
from pathlib import Path

from src.build_scopes import ScopeGraph, build_scope_graph
from src.scope_resolution import LocalImportStmt
from src.codeblocks import ImportBlock
from config import SupportedLangs


class RepoGraph:
    """
    Constructs a graph of the entire repository
    """

    def __init__(self, path: Path, lang: SupportedLangs = "python"):
        self.lang = lang
        self.scopes: Dict[str, ScopeGraph] = self.construct_scopes(path, lang)
        # self.scope_chunk_map: Dict[]
        for file in path.rglob("*.py"):
            g = build_scope_graph(file.read_bytes(), language=lang)
            imports = self.get_imports(g)
            print("Imports for file: ", str(file))
            for imp in imports:
                print(imp.module)
            # for imp in imports:
            #     print(imp)

    # TODO: add some sort of hierarchal structure to the scopes?
    def construct_scopes(self, path: Path, lang: str):
        """
        Returns all the scopes associated with the files in the directory
        """
        for file in path.rglob("*.py"):
            g = build_scope_graph(file.read_bytes(), language=lang)

    def construct_imports(self):
        # find the longest common prefix shared by all non-sys imports
        pass

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
