from src.build_scopes import build_scope_graph

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
from src.scope_resolution import (
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
"""

# test = """
# class A:
#     def func1():
#         a = 1
#         b = 2


# def func1():
#     a = 1
# """

scope_graph = build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
# module = Module(scope_graph)
# print(module.exports)
