from src.build_scopes import build_scope_graph
from src.languages import PythonParse
from src.scope_resolution.definition import LocalDef
from src.scope_resolution.scope import LocalScope
from src.build_scopes import ScopeGraph
from src.utils import TextRange


def test_insert_def():
    scope_graph = ScopeGraph(TextRange(start=1, end=6))

    # modeling the following code:
    #
    #     fn main() {
    #        let a = 2;
    #        let b = 3;
    #     }

    local_scope = LocalScope(1, 5)
    scope_graph.insert_local_scope(local_scope)

    # Insert a local definition
    local_def = LocalDef(start=2, end=3, symbol="a")
    scope_graph.insert_local_def(local_def)

    # Insert a hoisted definition
    hoisted_def = LocalDef(start=3, end=4, symbol="b")
    scope_graph.insert_hoisted_def(hoisted_def)

    # Insert a global definition
    global_def = LocalDef(start=4, end=5, symbol="global")
    scope_graph.insert_global_def(global_def)

    graph_state = """
1 --ScopeToScope-> 0
2 --DefToScope-> 1
3 --DefToScope-> 0
4 --DefToScope-> 0
"""

    assert scope_graph.to_str() == graph_state
