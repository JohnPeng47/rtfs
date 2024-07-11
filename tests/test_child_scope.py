from src.build_scopes import build_scope_graph
from src.scope_resolution.scope import LocalScope
from src.build_scopes import ScopeGraph
from src.utils import TextRange

from conftest import range


def test_child_scope():
    scope_graph = ScopeGraph(range(start=1, end=6))

    scope1 = LocalScope(range(start=1, end=5))
    scope2 = LocalScope(range(start=2, end=4))
    scope3 = LocalScope(range(start=3, end=4))
    scope4 = LocalScope(range(start=1, end=4))

    scope_graph.insert_local_scope(scope1)
    scope_graph.insert_local_scope(scope2)
    scope_graph.insert_local_scope(scope3)
    scope_graph.insert_local_scope(scope4)

    print(scope_graph.to_str())

    for child in scope_graph.child_scopes(1):
        print(child)
