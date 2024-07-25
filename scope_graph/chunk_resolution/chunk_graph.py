from networkx import DiGraph, node_link_graph
from pathlib import Path
from llama_index.core.schema import BaseNode
from typing import List, Tuple, Dict
import os

# from scope_graph.scope_resolution.interval_tree import IntervalGraph
from scope_graph.scope_resolution.capture_refs import capture_refs
from scope_graph.scope_resolution.graph_types import ScopeID
from scope_graph.repo_resolution.repo_graph import RepoGraph, RepoNodeID, repo_node_id
from scope_graph.fs import RepoFs
from scope_graph.utils import TextRange

from .graph import ChunkMetadata, ChunkNode, EdgeKind
from .cluster import cluster_leiden, cluster_infomap

import logging
from collections import defaultdict


logger = logging.getLogger(__name__)


class ChunkGraph:
    def __init__(self, repo_path: Path, g: DiGraph):
        self.fs = RepoFs(repo_path)
        self._graph = g
        self._repo_graph = RepoGraph(repo_path)
        self._file2scope = defaultdict(set)
        self._chunkmap: Dict[Path, List[ChunkNode]] = defaultdict(list)

    # TODO: design decisions
    # turn import => export mapping into a function
    # implement tqdm for chunk by chunk processing
    @classmethod
    def from_chunks(cls, repo_path: Path, chunks: List[BaseNode]):
        """
        Build chunk (import) to chunk (export) mapping by associating a chunk with
        the list of scopes, and then using the scope -> scope mapping provided in RepoGraph
        to resolve the exports
        """
        g = DiGraph()
        cg: ChunkGraph = cls(repo_path, g)
        cg._file2scope = defaultdict(set)

        # used to map range to chunks
        chunk_names = set()

        for i, chunk in enumerate(chunks, start=1):
            metadata = ChunkMetadata(**chunk.metadata)

            short_name = cg._chunk_short_name(chunk, i)
            chunk_names.add(short_name)
            chunk_node = ChunkNode(
                id=short_name,
                metadata=metadata,
                content=chunk.get_content(),
            )
            cg.add_node(chunk_node)

            cg._chunkmap[Path(metadata.file_path)].append(chunk_node)

        # shouldnt really happen but ...
        if len(chunk_names) != len(chunks):
            raise ValueError("Collision has occurred in chunk names")

        # main loop to build graph
        for chunk_node in cg.get_all_nodes():
            # chunk -> range -> scope
            cg.build_import_exports(chunk_node)

        for f, scopes in cg._file2scope.items():
            all_scopes = cg._repo_graph.scopes_map[f].scopes()
            all_scopes = set(all_scopes)

            unresolved = all_scopes - scopes
            print("Missing scopes: ", unresolved, " in ", f)

        return cg

    @classmethod
    def from_json(cls, repo_path: Path, json_data: Dict):
        cg = node_link_graph(json_data)

        return cls(repo_path, cg)

    def to_nodes(self, cluster: bool = True):
        if cluster:
            chunk2clusters, cluster2chunks = self.cluster()
            for cluster, chunks in cluster2chunks.items():
                for node in chunks:
                    # create a new node representing the cluster
                    node.set_community(chunk2clusters[node.id])

        return self.get_all_nodes()

    def get_node(self, node_id: str) -> ChunkNode:
        data = self._graph._node[node_id]

        # BUG: hacky fix but for some reason node_link_data stores
        # the data wihtout id
        if data.get("id", None):
            del data["id"]

        return ChunkNode(id=node_id, **self._graph._node[node_id])

    def get_all_nodes(self) -> List[ChunkNode]:
        return [self.get_node(n) for n in self._graph.nodes]

    def add_node(self, chunk_node: ChunkNode):
        id = chunk_node.id
        self._graph.add_node(id, **chunk_node.dict())

    def update_node(self, chunk_node: ChunkNode):
        self._graph.add_node(chunk_node)

    def build_import_exports(self, chunk_node: ChunkNode):
        """
        Build the import to export mapping for a chunk
        need to do: import (chunk -> range -> scope) -> export (scope -> range -> chunk)
        """
        file_path = Path(chunk_node.metadata.file_path)
        scope_graph = self._repo_graph.scopes_map[file_path]
        chunk_refs = capture_refs(chunk_node.content.encode())

        for ref in chunk_refs:
            # range -> scope
            ref_scope = scope_graph.scope_by_range(ref.range)
            # scope (import) -> scope (export)
            export_scopes = self._repo_graph.import_to_export_scope(
                repo_node_id(file_path, ref_scope)
            )

            print("Export scope len: ", len(export_scopes))

            # scope -> range -> chunk
            # decision:
            # 1. can resolve range here using the scope
            # 2. can resolve range when RepoNode is constructed
            # Favor 1. since we can use repo_graph for both scope->range and range->scope
            for export_scope, export_sg in [
                (node.scope, self._repo_graph.scopes_map[Path(node.file_path)])
                for node in export_scopes
            ]:
                export_range = export_sg.range_by_scope(export_scope)
                dst_chunk = self.find_chunk(file_path, export_range)
                if dst_chunk:
                    print("Adding edge: ", ref_scope, " -> ", dst_chunk.id)
                    self._graph.add_edge(
                        chunk_node.id, dst_chunk.id, kind=EdgeKind.ImportToExport
                    )

    # TODO: should really use IntervalGraph here but chunks are small enough
    def find_chunk(self, file_path: Path, range: TextRange):
        """
        Find a chunk given a range
        """
        chunks = self._chunkmap[file_path]
        for chunk in chunks:
            if chunk.range.contains_line(range):
                return chunk

        return None

    def to_str(self):
        repr = ""
        for u, v, _ in self._graph.edges(data=True):
            u_node = self.get_node(u)
            v_node = self.get_node(v)
            repr += f"{u_node} -> {v_node}\n"
        return repr

    def cluster(
        self, alg: str = "infomap"
    ) -> Tuple[Dict[ChunkNode, int], Dict[int, List[ChunkNode]]]:
        """
        Get the node cluster and remap it to ChunkNodes
        """
        node2cluster: Dict[ChunkNode, int] = {}
        cluster2node: Dict[int, List[ChunkNode]] = {}

        if alg == "leiden":
            chunk2clusters, cluster2chunks = cluster_leiden(self._graph)
        elif alg == "infomap":
            chunk2clusters, cluster2chunks = cluster_infomap(self._graph)

        return chunk2clusters, cluster2chunks

    def _chunk_short_name(self, chunk_node: BaseNode, i: int) -> str:
        # class_func = self._get_classes_and_funcs(
        #     Path(chunk_node.metadata["file_path"]), head_scope
        # )[0]

        filename = "/".join(chunk_node.metadata["file_path"].split(os.sep)[-2:])
        size = chunk_node.metadata["end_line"] - chunk_node.metadata["start_line"]
        # return f"{filename}.{class_func}.{size}"

        return f"{filename}#{i}.{size}"

    def _get_classes_and_funcs(
        self, file_path: Path, scope_id: ScopeID
    ) -> List[RepoNodeID]:
        def_nodes = self._repo_graph.scopes_map[file_path].definitions(scope_id)

        return list(
            filter(lambda d: d.data["def_type"] in ["class", "function"], def_nodes)
        )

    ##### For debugging ####!SECTION
    def nodes(self):
        return self._graph.nodes(data=True)

    # def get_import_refs(
    #     self, unresolved_refs: set[str], file_path: Path, scopes: List[ScopeID]
    # ):
    #     # get refs from the local scope that is a file-level import
    #     imported_refs = []
    #     file_imports = self._repo_graph.imports[file_path]

    #     for ref in unresolved_refs:
    #         if ref in [imp.namespace.child for imp in file_imports]:
    #             imported_refs.append(ref)

    #     return imported_refs

    # def unresolved_refs(
    #     self, file_path: Path, chunk_scopes: List[ScopeID]
    # ) -> Tuple[set, set]:
    #     """
    #     Find refs that
    #     """
    #     scope_graph = self.scopes_map[file_path]

    #     resolved = set()
    #     unresolved = set()

    #     # TODO: we also have the check definitions in the parent scope
    #     # TODO: also overlapped scopes/chunk ranges
    #     for scope in chunk_scopes:
    #         refs = [
    #             scope_graph.get_node(r).name
    #             for r in scope_graph.references_by_origin(scope)
    #         ]
    #         local_defs = [
    #             scope_graph.get_node(d).name for d in scope_graph.definitions(scope)
    #         ]

    #         # try to resolve refs with local defs
    #         for ref in refs:
    #             if ref in local_defs:
    #                 resolved.add(ref)
    #             else:
    #                 unresolved.add(ref)

    #     return resolved, unresolved

    # def get_modified_chunks(self):
    #     return self.chunks
