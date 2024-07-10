from dataclasses import dataclass

from src.utils import TextRange


@dataclass
class LocalImport:
    range: TextRange

    @classmethod
    def __init__(self, range: TextRange) -> "LocalImport":
        self.range = range

    def name(self, buffer: bytes) -> bytes:
        return buffer[self.range.start_byte : self.range.end_byte]
