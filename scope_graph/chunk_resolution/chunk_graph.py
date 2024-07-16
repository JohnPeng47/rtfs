from networkx import DiGraph
from pathlib import Path
from llama_index.core.schema import BaseNode
from typing import List, Tuple

from scope_graph.scope_resolution.graph import ScopeGraph, ScopeID
from scope_graph.repo_resolution.repo_graph import RepoGraph
from scope_graph.utils import TextRange
from scope_graph.fs import RepoFs

from .types import ChunkMetadata

import logging

logger = logging.getLogger(__name__)


class ChunkGraph:
    def __init__(self, repo_path: Path, chunks: List[BaseNode]):
        self.fs = RepoFs(repo_path)
        self._graph = DiGraph()
        self._repo_graph = RepoGraph(repo_path)

        # self.scopes_map = self._repo_graph.scopes_map
        # self.chunks = chunks
        # self.chunk_scope_map = {}

        # # TODO: rethink this whole block of code, should be just constructing import edges
        # for chunk in chunks:
        #     metadata = ChunkMetadata(**chunk.metadata)
        #     logger.info(f"________________ {metadata.file_name} ________________")
        #     chunk_scopes = self.get_scopes(
        #         Path(metadata.file_path),
        #         metadata.start_line,
        #         metadata.end_line,
        #     )
        #     resolved, unresolved = self.unresolved_refs(
        #         Path(metadata.file_path), chunk_scopes
        #     )
        #     logger.debug(f"Chunk: {chunk.get_content()}")
        #     logger.info(f"Chunk scopes: {chunk_scopes}")
        #     logger.info(f"Resolved: {resolved}")
        #     logger.info(f"Unresolved: {unresolved}")

        #     # try to resolve unresolved refs. every ref here
        #     # should lead to an edge to either:
        #     # - same file definition
        #     # - file-level import
        #     imported_refs = self.get_import_refs(
        #         unresolved, Path(metadata.file_path), chunk_scopes
        #     )
        #     logger.info(f"Imported refs: {imported_refs}")

        # TODO: construct graph to build graph

    def insert_chunks(self, chunks: List[BaseNode]):
        pass

    def get_scope_range(self, file: Path, range: TextRange) -> List[ScopeID]:
        return self.scopes_map[file].scopes_by_range(range, overlap=True)

    def get_scopes(self, file_path: Path, start_line: int, end_line: int):
        range = TextRange(
            start_byte=0,
            end_byte=0,
            start_point=(start_line, 0),
            end_point=(end_line, 0),
        )
        scope_graph = self.scopes_map[file_path]

        # TODO: note that we have potentially overlapping parent/child scopes here
        # alternative is to just return scopes, but this way we can
        # get definitions at the most granular child scope level
        chunk_scopes = set()
        scopes = scope_graph.scopes_by_range(range, overlap=True)
        for scope in scopes:
            child_scopes = scope_graph.child_scope_stack(scope)
            for child_scope in child_scopes:
                if range.contains_line(
                    scope_graph.get_node(child_scope).range, overlap=True
                ):
                    chunk_scopes.add(child_scope)

        return list(chunk_scopes)
        # return scopes

    def get_import_refs(
        self, unresolved_refs: set[str], file_path: Path, scopes: List[ScopeID]
    ):
        # get refs from the local scope that is a file-level import
        imported_refs = []
        file_imports = self._repo_graph.imports[file_path]

        for ref in unresolved_refs:
            if ref in [imp.namespace.child for imp in file_imports]:
                imported_refs.append(ref)

        return imported_refs

    def unresolved_refs(
        self, file_path: Path, chunk_scopes: List[ScopeID]
    ) -> Tuple[set, set]:
        """
        Find refs that
        """
        scope_graph = self.scopes_map[file_path]

        resolved = set()
        unresolved = set()

        # TODO: we also have the check definitions in the parent scope
        # TODO: also overlapped scopes/chunk ranges
        for scope in chunk_scopes:
            refs = [
                scope_graph.get_node(r).name
                for r in scope_graph.references_by_origin(scope)
            ]
            local_defs = [
                scope_graph.get_node(d).name for d in scope_graph.definitions(scope)
            ]

            # try to resolve refs with local defs
            for ref in refs:
                if ref in local_defs:
                    resolved.add(ref)
                else:
                    unresolved.add(ref)

        return resolved, unresolved

    def get_modified_chunks(self):
        return self.chunks
