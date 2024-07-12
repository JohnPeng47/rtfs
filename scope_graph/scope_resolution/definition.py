from dataclasses import dataclass
from typing import Optional

from scope_graph.utils import SymbolId, TextRange


@dataclass
class LocalDef:
    range: TextRange
    symbol: str
    name: str

    def __init__(
        self, range: TextRange, buffer: bytearray, symbol: Optional[str]
    ) -> "LocalDef":
        self.range = range
        self.symbol = symbol
        self.name = buffer[self.range.start_byte : self.range.end_byte].decode("utf-8")
