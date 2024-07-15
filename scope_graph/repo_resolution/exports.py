from scope_graph.repo_resolution.namespace import NameSpace
from scope_graph.build_scopes import ScopeID

from pathlib import Path


class Export:
    ns: NameSpace
    scope_id: ScopeID
    file_path: Path
