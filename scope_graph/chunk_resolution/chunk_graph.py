from networkx import DiGraph
from pathlib import Path
from llama_index.core.schema import BaseNode
from typing import List

from scope_graph.build_scopes import ScopeGraph, ScopeID
from scope_graph.repo_resolution.repo_graph import RepoGraph
from scope_graph.utils import TextRange


class ChunkGraph:
    def __init__(self, repo_path: Path, chunks: List[BaseNode]):
        self._graph = DiGraph()
        self._repo_graph = RepoGraph(repo_path)

        self.scopes_map = self._repo_graph.scopes_map
        self.chunks = chunks
        self.chunk_scope_map = {}

        for chunk in chunks:
            metadata = chunk.metadata
            scopes = self.get_scopes(
                metadata["file_path"], metadata["start_line"], metadata["end_line"]
            )

    def insert_chunks(self, chunks: List[BaseNode]):
        pass

    def get_scope_range(self, file: Path, range: TextRange) -> List[ScopeID]:
        return self.scopes_map[file].scopes_by_range(range, overlap=True)

    def get_scopes(self, file_path: str, start_line: int, end_line: int):
        range = TextRange(
            start_byte=0,
            end_byte=0,
            start_point=(start_line, 0),
            end_point=(end_line, 0),
        )

        scopes = self.get_scope_range(Path(file_path), range)
        # print(
        #     f"Found scopes: ",
        #     scopes,
        #     f"for range: {range.start_point.row}-{range.end_point.row}",
        # )

        # get refs tied to scopes
        for scope in scopes:
            pass

    def get_modified_chunks(self):
        return self.chunks
