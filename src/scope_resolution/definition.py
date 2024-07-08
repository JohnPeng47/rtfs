from dataclasses import dataclass
from typing import Optional

from src.utils import SymbolId, TextRange


@dataclass
class LocalDef:
    range: TextRange
    symbol_id: Optional[SymbolId]

    def __init__(self, range: TextRange, symbol_id: Optional[SymbolId]) -> "LocalDef":
        self.range = range
        self.symbol_id = symbol_id

    def name(self, buffer: bytes) -> bytes:
        return buffer[self.range.start : self.range.end]
