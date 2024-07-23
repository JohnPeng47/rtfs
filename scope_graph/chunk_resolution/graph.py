from enum import Enum
from typing import List, Optional
from pydantic.dataclasses import dataclass

from scope_graph.scope_resolution.graph import Node
from scope_graph.moatless.epic_split import CodeNode


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
    community: Optional[int] = None


class ChunkNode(Node):
    id: str
    metadata: ChunkMetadata
    scope_ids: List[int]
    content: str

    def set_community(self, community: int):
        self.metadata.community = community

    def __hash__(self):
        return hash(self.id + "".join(self.metadata.span_ids))

    def __str__(self):
        return f"{self.id}"

    def to_node(self):
        return CodeNode(
            id=self.id,
            text=self.content,
            metadata=self.metadata.__dict__,
            content=self.content,
        )


class EdgeKind(str, Enum):
    ImportToExport = "ImportToExport"
