from networkx import DiGraph, node_link_graph
from pathlib import Path
from llama_index.core.schema import BaseNode
from typing import List, Tuple, Dict
import os

from scope_graph.scope_resolution.graph import ScopeGraph, ScopeID
from scope_graph.repo_resolution.repo_graph import RepoGraph, RepoNodeID, repo_node_id
from scope_graph.utils import TextRange
from scope_graph.fs import RepoFs

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

    @classmethod
    def from_chunks(cls, repo_path: Path, chunks: List[BaseNode]):
        g = DiGraph()
        cg: ChunkGraph = cls(repo_path, g)

        scope2chunk: Dict[RepoNodeID, str] = {}  # maps repo node id to chunk id
        cg._file2scope = defaultdict(set)
        chunk_names = set()

        for i, chunk in enumerate(chunks, start=1):
            metadata = ChunkMetadata(**chunk.metadata)
            chunk_scopes = cg._get_chunk_scopes(
                Path(metadata.file_path),
                metadata.start_line,
                metadata.end_line,
            )

            short_name = cg._chunk_short_name(chunk, i)
            chunk_names.add(short_name)

            for scope in chunk_scopes:
                repo_id = repo_node_id(metadata.file_path, scope)
                scope2chunk[repo_id] = short_name

            cg.add_node(
                ChunkNode(
                    id=short_name,
                    metadata=metadata,
                    scope_ids=chunk_scopes,
                    content=chunk.get_content(),
                )
            )

        # shouldnt really happen but ...
        if len(chunk_names) != len(chunks):
            raise ValueError("Collision has occurred in chunk names")

        # get import_chunk -> scope -> scope -> export_chunk
        for node in cg.get_all_nodes():
            for scope in node.scope_ids:
                ref_ids = cg._repo_graph.get_export_refs(
                    repo_node_id(node.metadata.file_path, scope)
                )

                if ref_ids:
                    for exp_ref in ref_ids:
                        chunk_id = scope2chunk[exp_ref]
                        cg._graph.add_edge(
                            node.id, chunk_id, kind=EdgeKind.ImportToExport
                        )

        for f, scopes in cg._file2scope.items():
            all_scopes = cg._repo_graph.scopes_map[f].scopes()
            all_scopes = set(all_scopes)

            unresolved = all_scopes - scopes
            print("Missing scopes: ", unresolved, " in ", f)

        # logger.info(f"Chunk scopes: {chunk_scopes}")
        # logger.info(f"Resolved: {resolved}")
        # logger.info(f"Unresolved: {unresolved}")

        return cg

    @classmethod
    def from_json(cls, repo_path: Path, json_data: Dict):
        cg = node_link_graph(json_data)

        return cls(repo_path, cg)

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

    def get_scope_range(self, file: Path, range: TextRange) -> List[ScopeID]:
        return self._repo_graph.scopes_map[file].scopes_by_range(range, overlap=True)

    def _get_chunk_scopes(
        self, file_path: Path, start_line: int, end_line: int
    ) -> List[ScopeID]:
        print("Getting scopes for: ", start_line, end_line, file_path.name)

        range = TextRange(
            start_byte=0,
            end_byte=0,
            start_point=(start_line, 0),
            end_point=(end_line, 0),
        )

        scope_graph = self._repo_graph.scopes_map[file_path]

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
                    self._file2scope[file_path].add(child_scope)
                #     scope2file[child_scope].append(file_path)
                else:
                    scope_graph = self._repo_graph.scopes_map[file_path]
                    # print(
                    #     "Ignored scope: ",
                    #     child_scope,
                    #     scope_graph.get_node(child_scope).range.line_range(),
                    # )

        return list(chunk_scopes)
        # return scopes

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

        # node2cluster = {
        #     self.get_node(node_id): cluster
        #     for node_id, cluster in chunk2clusters.items()
        # }
        # cluster2node = {
        #     cluster: [self.get_node(node_id) for node_id in node_ids]
        #     for cluster, node_ids in cluster2chunks.items()
        # }

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
