from typing import Callable

from scope_graph.repo_resolution.repo_graph import RepoGraph
from conftest import repo_graph
import os

import pytest


@pytest.mark.parametrize(
    "repo_graph", ["tests/repos/small_repo"], indirect=["repo_graph"]
)
def test_imports(repo_graph: RepoGraph):
    sep = os.path.sep

    import1 = f"src.b.main2 local tests{sep}repos{sep}small_repo{sep}src{sep}b.py"
    import2 = f"src.b.main2 local tests{sep}repos{sep}small_repo{sep}src{sep}b.py"

    assert repo_graph._imports[1][1].__str__() == import1
    assert repo_graph._imports[2][1].__str__() == import2
