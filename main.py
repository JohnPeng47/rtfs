from scope_graph.build_scopes import build_scope_graph

from scope_graph.repo_resolution.repo_graph import RepoGraph
from pathlib import Path


## Failing tests
# Dotted assignment/ref
# test = """
# h.a = 1
# h.a = h.b

# def func1():
#     a = b
#     b = 2
# """

test = """
import b

class A:
    def func1():
        a = b()
        b = 2
"""

# scope_graph = build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
# print(scope_graph.to_str())

# print(scope_graph.to_str())
repo_graph = RepoGraph(Path("tests/repos/cowboy"))
# repo_graph.print_missing_imports()
# print(repo_graph.to_str())
