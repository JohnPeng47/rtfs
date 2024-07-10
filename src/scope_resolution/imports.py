from dataclasses import dataclass

from src.utils import TextRange


@dataclass
class LocalImport:
    range: TextRange
    name: str

    @classmethod
    def __init__(self, range: TextRange, buffer: bytearray) -> "LocalImport":
        self.range = range
        self.name = buffer[self.range.start_byte : self.range.end_byte].decode("utf-8")
