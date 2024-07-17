from dataclasses import dataclass
from pathlib import Path

from scope_graph.repo_resolution.namespace import NameSpace
from scope_graph.scope_resolution.graph import ScopeID


@dataclass
class Export:
    ns: NameSpace
    scope_id: ScopeID
    file_path: Path
