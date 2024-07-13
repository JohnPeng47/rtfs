from scope_graph.build_scopes import build_scope_graph
from scope_graph.languages import PythonParse
from scope_graph.scope_resolution.definition import LocalDef
from scope_graph.scope_resolution.scope import LocalScope
from scope_graph.build_scopes import ScopeGraph
from scope_graph.utils import TextRange


def test_insert_refs():
    test = """
import abc
a = 1

def func1(self):
    abc()
"""

    g = build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
    print(g.to_str())
