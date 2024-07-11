from dataclasses import dataclass, asdict
from typing import Optional, List

from src.utils import TextRange
from src.graph import NodeKind
from enum import Enum


class ModuleType(str, Enum):
    # a local package
    LOCAL = "local"
    # system/core lib
    SYS = "sys"
    # third party lib
    THIRD_PARTY = "third_party"


def parse_module(buffer: bytearray, range: TextRange) -> str:
    return buffer[range.start_byte : range.end_byte].decode("utf-8")


def parse_alias(buffer: bytearray, range: TextRange):
    return buffer[range.start_byte : range.end_byte].decode("utf-8")


def parse_name(buffer: bytearray, range: TextRange):
    return buffer[range.start_byte : range.end_byte].decode("utf-8")


class LocalImportStmt:
    """
    Represents a local import statement of the form:

    from module import name1, name2, name3 as alias
    """

    def __init__(
        self,
        range: TextRange,
        names: List[str],
        module: Optional[str] = "",
        aliases: Optional[List[str]] = [],
    ):
        self.range = range
        self.module = module
        self.aliases = aliases
        self.names = names

    # TODO: these are the serialization methods to convert to ScopeNode
    def to_node(self):
        json_node = {
            "range": self.range.dict(),
            "type": NodeKind.IMPORT,
            "data": {
                "module": self.module,
                "aliases": self.aliases,
                "names": self.names,
            },
        }
        # print("JSON_NODE: ", json_node)
        return json_node

    # Technically, this is the only python specific method
    def __str__(self):
        module_str = f"from {self.module} " if self.module else ""
        # TODO: fix this
        alias_str = f" as {self.aliases}" if self.aliases else ""
        names = ", ".join(self.names)
        # print(self.names)
        # print(names)

        return f"{module_str}import {names}{alias_str}"
