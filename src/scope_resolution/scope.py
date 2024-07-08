from dataclasses import dataclass
from typing import Optional, Iterator
from networkx import DiGraph

from src.graph import NodeKind, ScopeNode, EdgeKind
from src.utils import SymbolId, TextRange


@dataclass
class LocalScope:
    range: TextRange

    def __init__(self, start, end):
        self.range = TextRange(start, end)


class ScopeStack(Iterator):
    def __init__(self, scope_graph: DiGraph, start: Optional[int]):
        self.scope_graph = scope_graph
        self.start = start

    def __iter__(self) -> "ScopeStack":
        return self

    # TODO: fix the start parameter to return the root of the graph if not provided
    def __next__(self) -> int:
        if self.start is not None:
            original = self.start
            parent = None
            for _, target, attrs in self.scope_graph.out_edges(self.start, data=True):
                if (
                    attrs.get("type") == EdgeKind.ScopeToScope
                ):  # Replace with appropriate edge kind check
                    parent = target
                    break
            self.start = parent
            return original
        else:
            raise StopIteration
