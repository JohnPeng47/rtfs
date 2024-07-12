from src.repo_resolution.repo_graph import RepoGraph
from pathlib import Path


def test_import():
    g = RepoGraph(Path("tests/repos/small_repo"))

    for k, v in g.imports.items():
        for imp in v:
            assert str(imp.namespace) == "src.b.main2"
            assert imp.module_type == "local"
