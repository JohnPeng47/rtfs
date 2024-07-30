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
from scope_graph.graph import Node

from .graph import (
    ChunkMetadata,
    ClusterNode,
    ChunkNode,
    EdgeKind,
    ImportEdge,
    ClusterEdge,
    NodeKind,
    ChunkNodeID,
)
from .cluster import (
    cluster_leiden,
    cluster_infomap,
    gen_cluster_summaries,
    cluster_infomap_multilevel,
)

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
                og_id=chunk.node_id,
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

        return cg

    @classmethod
    def from_json(cls, repo_path: Path, json_data: Dict):
        cg = node_link_graph(json_data)

        return cls(repo_path, cg)

    def get_node(self, node_id: str) -> ChunkNode:
        data = self._graph._node.get(node_id, None)
        if not data:
            return None

        # BUG: hacky fix but for some reason node_link_data stores
        # the data wihtout id
        if data.get("id", None):
            del data["id"]

        if data["kind"] == NodeKind.Cluster:
            node = ClusterNode(id=node_id, **data)
        elif data["kind"] == NodeKind.Chunk:
            node = ChunkNode(id=node_id, **data)

        return node

    def get_all_nodes(self) -> List[ChunkNode]:
        return [self.get_node(n) for n in self._graph.nodes]

    def add_edge(self, n1, n2, edge: ImportEdge):
        self._graph.add_edge(n1, n2, **edge.dict())

    def add_node(self, node: Node):
        id = node.id
        self._graph.add_node(id, **node.dict())

    def update_node(self, chunk_node: ChunkNode):
        self._graph.add_node(chunk_node)

    def build_import_exports(self, chunk_node: ChunkNode):
        """
        Build the import to export mapping for a chunk
        need to do: import (chunk -> range -> scope) -> export (scope -> range -> chunk)
        """
        src_path = Path(chunk_node.metadata.file_path)
        scope_graph = self._repo_graph.scopes_map[src_path]
        chunk_refs = capture_refs(chunk_node.content.encode())

        for ref in chunk_refs:
            ref.range.add_line_offset(chunk_node.metadata.start_line)
            # range -> scope
            ref_scope = scope_graph.scope_by_range(ref.range)
            # scope (import) -> scope (export)
            export_scopes = self._repo_graph.import_to_export_scope(
                repo_node_id(src_path, ref_scope), ref.name
            )
            # scope -> range -> chunk
            # decision:
            # 1. can resolve range here using the scope
            # 2. can resolve range when RepoNode is constructed
            # Favor 1. since we can use repo_graph for both scope->range and range->scope
            for export_file, export_scope, export_sg in [
                (
                    node.file_path,
                    node.scope,
                    self._repo_graph.scopes_map[Path(node.file_path)],
                )
                for node in export_scopes
            ]:
                export_range = export_sg.range_by_scope(export_scope)
                dst_chunk = self.find_chunk(Path(export_file), export_range)

                if dst_chunk:
                    # print("Found chunk: ", dst_chunk.id, "with ref: ", ref.name)

                    edge = ImportEdge(ref=ref.name, kind=EdgeKind.ImportToExport)
                    self.add_edge(chunk_node.id, dst_chunk.id, edge)

    # TODO: should really use IntervalGraph here but chunks are small enough
    def find_chunk(self, file_path: Path, range: TextRange):
        """
        Find a chunk given a range
        """
        chunks = self._chunkmap[file_path]
        for chunk in chunks:
            if chunk.range.contains_line(range, overlap=True):
                return chunk

        return None

    def children(self, node_id: str):
        return [u for u, v, attrs in self._graph.edges(data=True) if v == node_id]

    def cluster(self, alg: str = "infomap") -> Dict[ChunkNodeID, Tuple]:
        """
        Get the node cluster and remap it to ChunkNodes
        """
        if alg == "infomap":
            cluster_dict = cluster_infomap(self._graph)
        else:
            raise Exception(f"{alg} not supported")

        # should we just store this dict?
        for chunk_node, clusters in cluster_dict.items():
            for i in range(len(clusters) - 1):
                # TODO: i lazy, not handle case where clusters[i: i+2] is len 1
                parent, child = clusters[i : i + 2]

                parent_id = f"{i}:{parent}"
                child_id = f"{i+1}:{child}"

                parent_node = self.get_node(parent_id)
                if not parent_node:
                    parent_node = ClusterNode(id=parent_id, depth=i)
                    self.add_node(parent_node)
                child_node = self.get_node(child_id)
                if not child_node:
                    child_node = ClusterNode(id=child_id, depth=i + 1)
                    self.add_node(child_node)

                self.add_edge(
                    child_id, parent_id, ClusterEdge(kind=EdgeKind.ClusterToCluster)
                )

            # last child_id is the cluster of chunk_node
            self.add_edge(
                chunk_node, child_id, ClusterEdge(kind=EdgeKind.NodeToCluster)
            )

        return cluster_dict

    def get_clusters(self, depth: int = None) -> List[ClusterNode]:
        cluster_nodes = [
            self.get_node(node)
            for node, attrs in self._graph.nodes(data=True)
            if attrs.get("kind", "") == "Cluster"
        ]
        if depth is not None:
            cluster_nodes = [node for node in cluster_nodes if node.depth == depth]

        return cluster_nodes

    def get_chunks_attached_to_clusters(self):
        from collections import Counter

        chunks_attached_to_clusters = {}
        clusters = defaultdict(int)

        total_chunks = len(
            [
                node
                for node, attrs in self._graph.nodes(data=True)
                if attrs["kind"] == "Chunk"
            ]
        )
        total_leaves = 0
        for u, v, attrs in self._graph.edges(data=True):
            if attrs.get("kind") == EdgeKind.NodeToCluster:
                chunk_node = self.get_node(u)
                cluster_node = self.get_node(v)

                if cluster_node.id not in chunks_attached_to_clusters:
                    chunks_attached_to_clusters[cluster_node.id] = []

                chunks_attached_to_clusters[cluster_node.id].append(chunk_node)
                clusters[cluster_node.id] += 1
                total_leaves += 1

        # for cluster, chunks in chunks_attached_to_clusters.items():
        #     print(f"---------------------{cluster}------------------")
        #     for chunk in chunks:
        #         print(chunk.id)
        #         print(chunk.content)
        #         print("--------------------------------------------------")

        print(f"Total chunks: {total_chunks}")
        print(f"Total leaves: {total_leaves}")

        return chunks_attached_to_clusters

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

    def to_str(self):
        repr = ""
        for u, v, attrs in self._graph.edges(data=True):
            ref = attrs["ref"]
            u_node = self.get_node(u)
            v_node = self.get_node(v)
            repr += (
                f"{u_node.metadata.file_name} --{ref}--> {v_node.metadata.file_name}\n"
            )
        return repr

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
