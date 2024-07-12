from scope_graph.build_scopes import build_scope_graph
from scope_graph.languages import PythonParse
from scope_graph.scope_resolution.scope import LocalScope
from scope_graph.build_scopes import ScopeGraph
from scope_graph.utils import TextRange


# def test_insert_local_scopes():
#     code = """
# def hello():
#     def goodbye():
#         a = 1
#     b = 2
# """
#     query, root_node = PythonParse._build_query(bytearray(code, encoding="utf-8"))
#     scope_graph = build_scope_graph(query, root_node, 0)


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

    scope_graph.insert_local_scope(scope1)
    scope_graph.insert_local_scope(scope2)
    scope_graph.insert_local_scope(scope3)
    scope_graph.insert_local_scope(scope4)

    graph_state = """
1 --ScopeToScope-> 0
2 --ScopeToScope-> 1
3 --ScopeToScope-> 2
4 --ScopeToScope-> 1
"""

    assert scope_graph.to_str() == graph_state
