from typing import TypeAlias
from pydantic import BaseModel

SymbolId: TypeAlias = str


class TextRange(BaseModel):
    start: int
    end: int

    def contains(self, range: "TextRange"):
        return range.start >= self.start and range.end <= self.end
