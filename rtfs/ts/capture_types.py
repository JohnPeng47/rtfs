from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

from rtfs.scope_resolution import Scoping


class LocalCallCapture(BaseModel):
    index: int
    name: str
    parameters: List[str] = []

    def add_parameter(self, value: str):
        self.parameters.append(value)


class LocalDefCapture(BaseModel):
    index: int
    symbol: Optional[str]
    scoping: Scoping


class LocalRefCapture(BaseModel):
    index: int
    symbol: Optional[str]


class ImportPartType(str, Enum):
    MODULE = "module"
    ALIAS = "alias"
    NAME = "name"


class LocalImportPartCapture(BaseModel):
    index: int
    part: str
