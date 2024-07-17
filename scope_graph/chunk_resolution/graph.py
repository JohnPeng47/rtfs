from scope_graph.scope_resolution.graph import Node

from enum import Enum


class ChunkNode(Node):
    id: str


class EdgeKind(str, Enum):
    ImportToExport = "ImportToExport"
