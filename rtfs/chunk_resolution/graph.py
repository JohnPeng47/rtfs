from enum import Enum
from typing import List, Optional, NewType, Literal
from pydantic.dataclasses import dataclass

from rtfs.graph import Node, Edge
from rtfs.moatless.epic_split import CodeNode
from rtfs.utils import TextRange

from .cluster import SummarizedChunk


ChunkNodeID = NewType("ChunkNodeID", str)
ClusterID = NewType("ClusterID", str)


@dataclass(kw_only=True)
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


class NodeKind(str, Enum):
    Chunk = "Chunk"
    Cluster = "Cluster"

@dataclass(kw_only=True)
class ChunkNode(Node):
    id: ChunkNodeID
    og_id: str  # original ID on the BaseNode
    metadata: ChunkMetadata
    content: str
    kind: NodeKind = NodeKind.Chunk

    @property
    def range(self):
        return TextRange(
            start_byte=0,
            end_byte=0,
            # NOTE: subtract 1 to convert to 0-based to conform with TreeSitter 0 based indexing
            start_point=(self.metadata.start_line - 1, 0),
            end_point=(self.metadata.end_line - 1, 0),
        )

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

    def get_content(self):
        return self.content

@dataclass(kw_only=True)
class ClusterNode(Node):
    id: ClusterID
    kind: NodeKind = NodeKind.Cluster
    summary_data: Optional[SummarizedChunk] = None

    def get_content(self):
        return self.summary_data.summary if self.summary_data else ""

    def __hash__(self):
        return sum([ord(c) for c in self.id])


class ClusterEdgeKind(str, Enum):
    ChunkToChunk = "ChunkToChunk"
    ClusterToCluster = "ClusterToCluster"
    ChunkToCluster = "ChunkToCluster"

class ChunkEdgeKind(str, Enum):
    ImportFrom = "ImportFrom"
    CallTo = "CallTo"

@dataclass(kw_only=True)
class ImportEdge(Edge):
    kind: ChunkEdgeKind = ChunkEdgeKind.ImportFrom
    ref: str

@dataclass(kw_only=True)
class CallEdge(Edge):
    kind: ChunkEdgeKind = ChunkEdgeKind.CallTo
    ref: str

@dataclass(kw_only=True)
class ClusterEdge(Edge):
    kind: Literal[ClusterEdgeKind.ClusterToCluster, ClusterEdgeKind.ChunkToCluster]
