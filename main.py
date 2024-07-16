from scope_graph.build_scopes import build_scope_graph

from scope_graph.repo_resolution.repo_graph import RepoGraph
from pathlib import Path


### Failing tests
# Dotted assignment/ref
test = """
h.a = 1
h.a = h.b

def func1():
    a = 1
    b = 2
"""


# test = open("tests/repos/test-import-ref/parser.py", "rb").read()
scope_graph = build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
print(scope_graph.to_str())

# repo_graph = RepoGraph(Path("tests/repos/test-import-ref"))
