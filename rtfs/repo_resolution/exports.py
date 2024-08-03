from dataclasses import dataclass
from pathlib import Path

from rtfs.repo_resolution.namespace import NameSpace
from rtfs.scope_resolution.graph_types import ScopeID


@dataclass
class Export:
    namespace: NameSpace
    scope_id: ScopeID
    file_path: Path
