from dataclasses import dataclass
from typing import Optional

from src.utils import SymbolId, TextRange


@dataclass
class LocalDef:
    range: TextRange
    symbol: str

    def __init__(self, range: TextRange, symbol: Optional[str]) -> "LocalDef":
        self.range = range
        self.symbol = symbol

    def name(self, buffer: bytes) -> bytes:
        return buffer[self.range.start : self.range.end]
