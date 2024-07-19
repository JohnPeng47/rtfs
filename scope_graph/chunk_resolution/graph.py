from enum import Enum
from typing import List, Optional
from pydantic.dataclasses import dataclass

from scope_graph.scope_resolution.graph import Node


@dataclass
class ChunkMetadata:
    file_path: str
    file_name: str
    file_type: str
    category: str
    tokens: int
    span_ids: List[str]
    start_line: int
    end_line: int


class ChunkNode(Node):
    id: str
    metadata: ChunkMetadata
    scope_ids: List[int]
    content: str

    def __hash__(self):
        return hash(self.id + "".join(self.metadata.span_ids))

    def __str__(self):
        return f"{self.id}"


class EdgeKind(str, Enum):
    ImportToExport = "ImportToExport"
