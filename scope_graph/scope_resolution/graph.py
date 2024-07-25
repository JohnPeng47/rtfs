from networkx import DiGraph, dfs_postorder_nodes
from typing import Dict, Optional, Iterator, List, NewType, Tuple
from enum import Enum
from collections import defaultdict

from scope_graph.graph import Node
from scope_graph.utils import TextRange

from .imports import LocalImportStmt
from .definition import LocalDef
from .reference import Reference
from .scope import LocalScope, ScopeStack
from .graph_types import NodeKind, EdgeKind, ScopeNode, ScopeID
from .interval_tree import IntervalGraph


class ScopeGraph:
    def __init__(self, range: TextRange):
        # TODO: put all this logic into a separate Graph class
        self._graph = DiGraph()
        self._node_counter = 0

        self.scope2range: Dict[ScopeID, TextRange] = {}

        root_scope = ScopeNode(range=range, type=NodeKind.SCOPE)
        self.root_idx = self.add_node(root_scope)
        self.scope2range[self.root_idx] = range

        # use this to faster resolve range -> scope queries
        self._ig = IntervalGraph(range, self.root_idx)

    def insert_local_scope(self, new: LocalScope):
        """
        Insert local scope to smallest enclosing parent scope
        """
        parent_scope = self.scope_by_range(new.range, self.root_idx)
        if parent_scope is not None:
            new_node = ScopeNode(range=new.range, type=NodeKind.SCOPE)
            new_id = self.add_node(new_node)
            self._graph.add_edge(new_id, parent_scope, type=EdgeKind.ScopeToScope)
            self._ig.add_scope(new.range, new_id)

            self.scope2range[new_id] = new.range

    def insert_local_import(self, new: LocalImportStmt):
        """
        Insert import into smallest enclosing parent scope
        """
        parent_scope = self.scope_by_range(new.range, self.root_idx)
        if parent_scope is not None:
            new_node = ScopeNode(
                range=new.range,
                type=NodeKind.IMPORT,
                data={
                    "from_name": new.from_name,
                    "aliases": new.aliases,
                    "names": new.names,
                },
            )

            new_id = self.add_node(new_node)
            self._graph.add_edge(new_id, parent_scope, type=EdgeKind.ImportToScope)

    def insert_local_def(self, new: LocalDef) -> None:
        """
        Insert a def into the scope-graph
        """
        defining_scope = self.scope_by_range(new.range, self.root_idx)
        if defining_scope is not None:
            new_def = ScopeNode(
                range=new.range,
                name=new.name,
                type=NodeKind.DEFINITION,
                data={"def_type": new.symbol},
            )
            new_idx = self.add_node(new_def)
            self._graph.add_edge(new_idx, defining_scope, type=EdgeKind.DefToScope)

    def insert_hoisted_def(self, new: LocalDef) -> None:
        """
        Insert a def into the scope-graph, at the parent scope of the defining scope
        """
        defining_scope = self.scope_by_range(new.range, self.root_idx)
        if defining_scope is not None:
            def_type = new.symbol
            new_def = ScopeNode(
                range=new.range,
                name=new.name,
                type=NodeKind.DEFINITION,
            )
            new_idx = self.add_node(new_def)

            # if the parent scope exists, insert this def there, if not,
            # insert into the defining scope
            parent_scope = self.parent_scope(defining_scope)
            target_scope = parent_scope if parent_scope is not None else defining_scope

            self._graph.add_edge(new_idx, target_scope, type=EdgeKind.DefToScope)

    def insert_global_def(self, new: LocalDef) -> None:
        """
        Insert a def into the scope-graph, at the root scope
        """
        new_def = ScopeNode(
            range=new.range,
            name=new.name,
            type=NodeKind.DEFINITION,
        )
        new_idx = self.add_node(new_def)
        self._graph.add_edge(new_idx, self.root_idx, type=EdgeKind.DefToScope)

    def insert_ref(self, new: Reference) -> None:
        possible_defs = []
        possible_imports = []

        local_scope_idx = self.scope_by_range(new.range, self.root_idx)
        if local_scope_idx is not None:
            # traverse the scopes from the current-scope to the root-scope
            for scope in self.parent_scope_stack(local_scope_idx):
                # find candidate definitions in each scope
                for local_def in [
                    src
                    for src, dst, attrs in self._graph.in_edges(scope, data=True)
                    if attrs["type"] == EdgeKind.DefToScope
                ]:
                    def_node = self.get_node(local_def)
                    if def_node.type == NodeKind.DEFINITION:
                        if new.name == def_node.name:
                            possible_defs.append((local_def, def_node.name))
                            break  # ensure that we add the first definition in the nearest ancestor scope

                # find candidate imports in each scope
                # TODO: fix this for new import names format
                for local_import in [
                    src
                    for src, dst, attrs in self._graph.in_edges(scope, data=True)
                    if attrs["type"] == EdgeKind.ImportToScope
                ]:
                    import_node = self.get_node(local_import)
                    if import_node.type == NodeKind.IMPORT:
                        if new.name in import_node.data["names"]:
                            possible_imports.append((local_import, import_node.name))

        if possible_defs or possible_imports:
            new_ref = ScopeNode(range=new.range, name=new.name, type=NodeKind.REFERENCE)
            ref_idx = self.add_node(new_ref)

            for def_idx, _ in possible_defs:
                self._graph.add_edge(ref_idx, def_idx, type=EdgeKind.RefToDef)

            for imp_idx, _ in possible_imports:
                self._graph.add_edge(ref_idx, imp_idx, type=EdgeKind.RefToImport)

            # add an edge back to the originating scope of the reference
            self._graph.add_edge(ref_idx, local_scope_idx, type=EdgeKind.RefToOrigin)

    # TODO: maybe we want to think about another class for sticking all these utility access methods
    def scopes(self) -> List[ScopeID]:
        """
        Return all scopes in the graph
        """
        return [
            u
            for u, attrs in self._graph.nodes(data=True)
            if attrs["type"] == NodeKind.SCOPE
        ]

    def imports(self, start: int) -> List[int]:
        """
        Get all imports in the scope
        """
        return [
            u
            for u, v, attrs in self._graph.in_edges(start, data=True)
            if attrs["type"] == EdgeKind.ImportToScope
        ]

    def get_all_imports(self) -> List[ScopeNode]:
        all_imports = []

        scopes = self.scopes()
        for scope in scopes:
            all_imports.extend([self.get_node(i) for i in self.imports(scope)])

        return all_imports

    def definitions(self, start: int) -> List[ScopeNode]:
        """
        Get all definitions in the scope and child scope
        """
        return [
            self.get_node(u)
            for u, v, attrs in self._graph.in_edges(start, data=True)
            if attrs["type"] == EdgeKind.DefToScope
        ]

    def get_all_definitions(self) -> List[ScopeNode]:
        all_defs = []

        scopes = self.scopes()
        for scope in scopes:
            all_defs.extend(self.definitions(scope))

        return all_defs

    def references_by_origin(self, start: int) -> List[int]:
        """
        Get all references in the scope and child scope
        """
        return [
            u
            for u, v, attrs in self._graph.in_edges(start, data=True)
            if attrs["type"] == EdgeKind.RefToOrigin
        ]

    def child_scopes(self, start: ScopeID) -> List[ScopeID]:
        """
        Get all child scopes of the given scope
        """
        return [
            u
            for u, v, attrs in self._graph.edges(data=True)
            if attrs["type"] == EdgeKind.ScopeToScope and v == start
        ]

    def parent_scope(self, start: ScopeID) -> Optional[ScopeID]:
        """
        Produce the parent scope of a given scope
        """
        if self.get_node(start).type == NodeKind.SCOPE:
            for src, dst, attrs in self._graph.out_edges(start, data=True):
                if attrs["type"] == EdgeKind.ScopeToScope:
                    return dst
        return None

    # def scope_by_range(self, range: TextRange, start: ScopeID = None) -> ScopeID:
    #     """
    #     Returns the smallest child
    #     """
    #     print(f"Finding scope by range: {range.line_range()}")
    #     node = self.get_node(start)
    #     if node.range.contains_line(range):
    #         print(f"Scope {node.range.line_range()} contains {range.line_range()}")
    #         for child_id, attrs in [
    #             (src, attrs)
    #             for src, dst, attrs in self._graph.in_edges(start, data=True)
    #             if attrs["type"] == EdgeKind.ScopeToScope
    #         ]:
    #             if child := self.scope_by_range(range, child_id):
    #                 return child
    #         return start

    #     return None

    def scope_by_range(
        self, range: TextRange, start: ScopeID = None
    ) -> Optional[ScopeID]:
        """
        Returns the smallest child scope that contains the given range
        """
        if not start:
            start = self.root_idx

        resolved_scope_id = self._ig.contains(range, overlap=False)
        if resolved_scope_id is not None:
            return resolved_scope_id

        return start

    def range_by_scope(self, scope: ScopeID) -> Optional[TextRange]:
        """
        Returns the range of a scope
        """
        return self.scope2range.get(scope, None)

    def child_scope_stack(self, start: ScopeID) -> List[ScopeID]:
        stack = self.child_scopes(start)

        for child in self.child_scopes(start):
            stack += self.child_scope_stack(child)

        return stack

    def get_leaf_children(self, start: ScopeID) -> Iterator[ScopeID]:
        """
        Finds all the leaf children reachable from the given scope
        """
        # Use DFS to find all reachable nodes
        for node in dfs_postorder_nodes(self._graph, start):
            if self._graph.out_degree(node) == 0:  # for directed graphs
                yield node

    def parent_scope_stack(self, start: ScopeID):
        """
        Returns stack of parent scope traversed
        """
        return ScopeStack(self._graph, start)

    def add_node(self, node: ScopeNode) -> int:
        """
        Adds node and increments node_counter for its id
        """
        id = self._node_counter
        self._graph.add_node(id, **node.dict())

        self._node_counter += 1

        return id

    def get_node(self, idx: int) -> ScopeNode:
        return ScopeNode(**self._graph.nodes(data=True)[idx])

    def to_str(self):
        """
        A str representation of the graph
        """
        repr = "\n"

        for u, v, attrs in self._graph.edges(data=True):
            edge_type = attrs["type"]
            u_data = ""
            v_data = ""

            if (
                edge_type == EdgeKind.RefToDef
                or edge_type == EdgeKind.RefToImport
                or EdgeKind.DefToScope
            ):
                u_data = self.get_node(u).name
                v_data = self.get_node(v).name

            repr += f"{u}:{u_data} --{edge_type}-> {v}:{v_data}\n"

        return repr
