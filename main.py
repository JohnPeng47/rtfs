from scope_graph.build_scopes import build_scope_graph

from scope_graph.repo_resolution.repo_graph import RepoGraph
from pathlib import Path

# test = """
# import namespace.abc

# class Hello:
#     def hello1(self):
#         self.a = 1
#         pass

#     def panzer(self):
#         pass
# """
test = """
from scope_graph.scope_resolution import (
    LocalScope,
    LocalDef,
    LocalImportStmt,
    Reference,
    ScopeStack,
)
from abc import ABC, abstractmethod
import abc
from .a import abc

h = 1

def func1():
    a = 1
    b = 2
    def func2():
        c = 2
"""

# test = """
# class A:
#     def func1():
#         a = 1
#         b = 2


# def func1():
#     a = 1
# """

## Single file test

# test = open("tests/repos/test-import-ref/parser.py", "rb").read()
scope_graph = build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
print(scope_graph.to_str())

# repo_graph = RepoGraph(Path("tests/repos/test-import-ref"))
