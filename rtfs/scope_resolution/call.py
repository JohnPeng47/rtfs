# rtfs/scope_resolution/call.py

from dataclasses import dataclass, field
from typing import List, Optional

from rtfs.utils import TextRange


@dataclass
class LocalCall:
    range: TextRange
    name: str
    parameters: List[str] = field(default_factory=list)

    def __init__(
        self, range: TextRange, name: str, parameters: List[str] = None
    ) -> None:
        self.range = range
        self.name = name
        self.parameters = parameters if parameters is not None else []

    def to_node(self):
        return {
            "name": self.name,
            "range": self.range.dict(),
            "type": "Call",
            "data": {"parameters": self.parameters},
        }
