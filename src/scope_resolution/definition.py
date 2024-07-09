from dataclasses import dataclass
from typing import Optional

from src.utils import SymbolId, TextRange


@dataclass
class LocalDef:
    range: TextRange
    symbol: str

    def __init__(self, start, end, symbol: Optional[str]) -> "LocalDef":
        self.range = TextRange(start=start, end=end)
        self.symbol = symbol

    def name(self, buffer: bytes) -> bytes:
        return buffer[self.range.start : self.range.end]
