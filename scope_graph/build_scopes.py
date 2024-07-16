from pydantic import BaseModel
from typing import Dict, Optional, List
from enum import Enum

from scope_graph.scope_resolution import LocalScope, LocalDef, Reference, Scoping
from scope_graph.scope_resolution.imports import (
    LocalImportStmt,
    parse_from,
    parse_alias,
    parse_name,
)
from scope_graph.utils import TextRange
from scope_graph.languages import LANG_PARSER
from scope_graph.scope_resolution.graph import ScopeGraph


# TODO: make this a part of TSLangConfig
namespaces = ["class", "function", "parameter", "variable"]


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
