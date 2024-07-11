from dataclasses import dataclass, asdict
from typing import Optional, List

from src.utils import TextRange


@dataclass
class LocalImportStmt:
    range: TextRange
    names: List[str]
    module: Optional[str]
    alias: Optional[str]

    def __init__(self, range: TextRange) -> "LocalImportStmt":
        self.range = range
        self.module = ""
        self.alias = ""
        self.names = []

    def set_module(self, buffer: str, range: TextRange):
        self.module = buffer[range.start_byte : range.end_byte].decode("utf-8")

    def set_alias(self, buffer: str, range: TextRange):
        self.alias = buffer[range.start_byte : range.end_byte].decode("utf-8")

    def add_name(self, buffer: str, range: TextRange):
        self.names.append(buffer[range.start_byte : range.end_byte].decode("utf-8"))

    # TODO: these are the serialization methods to convert to ScopeNode
    def to_data(self):
        return asdict(self)

    @classmethod
    def from_data(cls, range, data):
        localImport = cls(range)
        localImport.module = data["module"]
        localImport.alias = data["alias"]
        localImport.names = data["names"]

        return localImport

    # Technically, this is the only python specific method
    def __str__(self):
        module_str = f"from {self.module} " if self.module else ""
        alias_str = f" as {self.alias}" if self.alias else ""
        names = ", ".join(self.names)

        return f"{module_str}import {names}{alias_str}"
