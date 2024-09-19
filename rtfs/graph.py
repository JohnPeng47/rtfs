from dataclasses import dataclass, field
from networkx import DiGraph
from typing import List, Type, Dict
import uuid


class DictMixin:
    def dict(self):
        return {k: v for k, v in self.__dict__.items() if not k == "id"}


@dataclass
class Node(DictMixin):
    kind: str
    id: str = field(default=str(uuid.uuid4()))


@dataclass
class Edge(DictMixin):
    src: str
    dst: str


class CodeGraph(DiGraph):
    def __init__(self, *, node_types: List[Type[Node]]):
        super().__init__()
        self._graph = DiGraph()
        self.node_types: Dict[str, Type[Node]] = {nt.__name__: nt for nt in node_types}

    def has_node(self, node_id: str) -> bool:
        return self._graph.has_node(node_id)

    def add_node(self, node: Node):
        self._graph.add_node(node.id, **node.dict())
        return node.id

    def add_edge(self, edge: Edge):
        self._graph.add_edge(edge.src, edge.dst, **edge.dict())

    def get_node(self, node_id: str) -> Node:
        if not self._graph.has_node(node_id):
            return None

        node_data = self._graph.nodes[node_id]
        node_kind = node_data.get("kind")

        if node_kind not in self.node_types:
            raise ValueError(f"Unknown node kind: {node_kind}")

        node_class = self.node_types[node_kind]
        return node_class(id=node_id, **node_data)
