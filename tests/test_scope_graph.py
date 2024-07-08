from src.build_scopes import build_scope_graph
from src.languages import PythonParse
from src.scope_resolution.scope import LocalScope
from src.build_scopes import ScopeGraph
from src.utils import TextRange


def test_insert_local_scopes():
    code = """
def hello():
    def goodbye():
        a = 1
    b = 2
"""
    query, root_node = PythonParse._build_query(bytearray(code, encoding="utf-8"))
    scope_graph = build_scope_graph(query, root_node, 0)


def test_insert_scope():
    scope_graph = ScopeGraph(TextRange(start=1, end=6))

    # scope 1:
    #   -> scope2
    #       -> scope 3
    #   -> scope 4
    scope1 = LocalScope(1, 5)
    scope2 = LocalScope(2, 4)
    scope3 = LocalScope(3, 4)
    scope4 = LocalScope(1, 4)

    id_1 = scope_graph.insert_local_scope(scope1)
    id_2 = scope_graph.insert_local_scope(scope2)
    id_3 = scope_graph.insert_local_scope(scope3)
    id_4 = scope_graph.insert_local_scope(scope4)

    _, parent_2 = list(scope_graph._graph.out_edges(id_2))[0]
    assert parent_2 == id_1

    _, parent_3 = list(scope_graph._graph.out_edges(id_3))[0]
    assert parent_3 == id_2

    _, parent_4 = list(scope_graph._graph.out_edges(id_4))[0]
    assert parent_4 == id_1
