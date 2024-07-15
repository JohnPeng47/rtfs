from pydantic import BaseModel
from networkx import DiGraph

from typing import Dict, Optional, Iterator, List, NewType, Tuple
from enum import Enum

from scope_graph.scope_resolution import LocalScope, LocalDef, Reference, ScopeStack
from scope_graph.scope_resolution.imports import (
    LocalImportStmt,
    parse_from,
    parse_alias,
    parse_name,
)
from scope_graph.graph import ScopeNode, NodeKind, EdgeKind
from scope_graph.utils import TextRange
from scope_graph.languages import LANG_PARSER


ScopeID = NewType("ScopeID", int)


class Scoping(str, Enum):
    GLOBAL = "global"
    HOISTED = "hoist"
    LOCAL = "local"


# TODO: make this a part
namespaces = ["class", "function", "parameter", "variable"]


class ScopeGraph:
    def __init__(self, range: TextRange):
        # TODO: put all this logic into a separate Graph class
        self._graph = DiGraph()
        self._node_counter = 0

        self.root_idx = self.add_node(ScopeNode(range=range, type=NodeKind.SCOPE))

    def insert_local_scope(self, new: LocalScope):
        """
        Insert local scope to smallest enclosing parent scope
        """
        parent_scope = self.scope_by_range(new.range, self.root_idx)
        if parent_scope is not None:
            new_node = ScopeNode(range=new.range, type=NodeKind.SCOPE)
            new_id = self.add_node(new_node)
            self._graph.add_edge(new_id, parent_scope, type=EdgeKind.ScopeToScope)

    def insert_local_import(self, new: LocalImportStmt):
        """
        Insert import into smallest enclosing parent scope
        """
        parent_scope = self.scope_by_range(new.range, self.root_idx)
        if parent_scope is not None:
            new_node = ScopeNode(**new.to_node())

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
            for scope in self.scope_stack(local_scope_idx):
                # find candidate definitions in each scope
                for local_def in [
                    src
                    for src, dst, attrs in self._graph.in_edges(scope, data=True)
                    if attrs["type"] == EdgeKind.DefToScope
                ]:
                    def_node = self.get_node(local_def)
                    if def_node.type == NodeKind.DEFINITION:
                        # print("New: ", new.name, "Def: ", def_node.name)

                        # ensure that we add the first definition in the nearest ancestor scope
                        if new.name == def_node.name and new.name not in [
                            name for id, name in possible_defs
                        ]:
                            # if (
                            #     def_node.symbol_id is None
                            #     or new.symbol_id is None
                            #     or def_node.symbol_id.namespace_idx
                            #     == new.symbol_id.namespace_idx
                            # ):
                            possible_defs.append((local_def, def_node.name))

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

    def scopes(self) -> List[ScopeID]:
        """
        Return all scopes in the graph
        """
        return [
            u
            for u, attrs in self._graph.nodes(data=True)
            if attrs["type"] == NodeKind.SCOPE
        ]

    def scopes_by_range(self, range: TextRange, overlap=False) -> List[ScopeID]:
        """
        Get all scopes that contain the given range
        """
        return [
            u
            for u, attrs in self._graph.nodes(data=True)
            if attrs["type"] == NodeKind.SCOPE
            and self.get_node(u).range.contains_line(range, overlap=overlap)
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

    def definitions(self, start: int) -> List[int]:
        """
        Get all definitions in the scope and child scope
        """
        return [
            u
            for u, v, attrs in self._graph.in_edges(start, data=True)
            if attrs["type"] == EdgeKind.DefToScope
        ]

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

    def scope_by_range(self, range: TextRange, start: ScopeID) -> ScopeID:
        """
        Returns the smallest child
        """
        node = self.get_node(start)
        if node.range.contains(range):
            for child_id, attrs in [
                (src, attrs)
                for src, dst, attrs in self._graph.in_edges(start, data=True)
                if attrs["type"] == EdgeKind.ScopeToScope
            ]:
                if child := self.scope_by_range(range, child_id):
                    return child
            return start

        return None

    def scope_stack(self, start: ScopeID):
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


####### Parsing Scopes ########


class LocalDefCapture(BaseModel):
    index: int
    symbol: Optional[str]
    scoping: Scoping


class LocalRefCapture(BaseModel):
    index: int
    symbol: Optional[str]


class ImportPartType(str, Enum):
    MODULE = "module"
    ALIAS = "alias"
    NAME = "name"


class LocalImportPartCapture(BaseModel):
    index: int
    part: str


def build_scope_graph(src_bytes: bytearray, language: str = "python") -> ScopeGraph:
    parser = LANG_PARSER[language]
    query, root_node = parser._build_query(src_bytes)

    local_def_captures: List[LocalDefCapture] = []
    local_ref_captures: List[LocalRefCapture] = []
    local_scope_capture_indices: List = []
    local_import_stmt_capture_indices: List = []
    local_import_part_capture: List[LocalImportPartCapture] = []

    # capture_id -> range map
    capture_map: Dict[int, TextRange] = {}

    for i, (node, capture_name) in enumerate(query.captures(root_node)):
        capture_map[i] = TextRange(
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            start_point=node.start_point,
            end_point=node.end_point,
        )

        parts = capture_name.split(".")
        # print(node, capture_name, parts)
        match parts:
            case [scoping, "definition", sym]:
                index = i
                symbol = sym
                scoping_enum = Scoping(scoping)

                l = LocalDefCapture(
                    index=index,
                    symbol=symbol,
                    scoping=scoping_enum,
                )
                local_def_captures.append(l)
            case [scoping, "definition"]:
                index = i
                symbol = None
                scoping_enum = Scoping(scoping)

                l = LocalDefCapture(
                    index=index,
                    symbol=symbol,
                    scoping=scoping_enum,
                )
                local_def_captures.append(l)
            case ["local", "reference", sym]:
                index = i
                symbol = sym

                l = LocalRefCapture(index=index, symbol=symbol)
                local_ref_captures.append(l)
            case ["local", "reference"]:
                index = i
                symbol = None

                l = LocalRefCapture(index=index, symbol=symbol)
                local_ref_captures.append(l)
            case ["local", "scope"]:
                local_scope_capture_indices.append(i)
            case ["local", "import", "statement"]:
                local_import_stmt_capture_indices.append(i)
            case ["local", "import", part]:
                l = LocalImportPartCapture(index=i, part=part)
                local_import_part_capture.append(l)

    root_range = TextRange(
        start_byte=root_node.start_byte,
        end_byte=root_node.end_byte,
        start_point=root_node.start_point,
        end_point=root_node.end_point,
    )
    scope_graph = ScopeGraph(root_range)

    # insert scopes first
    for i in local_scope_capture_indices:
        scope_graph.insert_local_scope(LocalScope(capture_map[i]))

    # insert imports
    for i in local_import_stmt_capture_indices:
        range = capture_map[i]
        from_name, aliases, names = "", [], []
        for part in local_import_part_capture:
            part_range = capture_map[part.index]
            if range.contains(part_range):
                match part.part:
                    case ImportPartType.MODULE:
                        from_name = parse_from(src_bytes, part_range)
                    case ImportPartType.ALIAS:
                        aliases.append(parse_alias(src_bytes, part_range))
                    case ImportPartType.NAME:
                        names.append(parse_name(src_bytes, part_range))

        import_stmt = LocalImportStmt(
            range, names, from_name=from_name, aliases=aliases
        )
        scope_graph.insert_local_import(import_stmt)

    # insert defs
    for def_capture in local_def_captures:
        range = capture_map[def_capture.index]
        local_def = LocalDef(range, src_bytes, def_capture.symbol)
        match def_capture.scoping:
            case Scoping.GLOBAL:
                scope_graph.insert_global_def(local_def)
            case Scoping.HOISTED:
                scope_graph.insert_hoisted_def(local_def)
            case Scoping.LOCAL:
                scope_graph.insert_local_def(local_def)

    # insert refs
    for local_ref_capture in local_ref_captures:
        index = local_ref_capture.index
        symbol = local_ref_capture.symbol

        range = capture_map[index]
        # if the symbol is present, is it one of the supported symbols for this language?
        symbol_id = symbol if symbol in namespaces else None
        new_ref = Reference(range, src_bytes, symbol_id=symbol_id)

        scope_graph.insert_ref(new_ref)

    return scope_graph
