from dataclasses import dataclass

from src.utils import TextRange


@dataclass
class LocalImport:
    range: TextRange

    @classmethod
    def __init__(self, start, end) -> "LocalImport":
        self.range = TextRange(start=start, end=end)

    def name(self, buffer: bytes) -> bytes:
        return buffer[self.range.start : self.range.end]
