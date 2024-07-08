from typing import TypeAlias
from dataclasses import dataclass

SymbolId: TypeAlias = str


@dataclass
class TextRange:
    start: int
    end: int

    def contains(self, range: "TextRange"):
        return range.start >= self.start and range.end <= self.end
