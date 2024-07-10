from src.languages.python.python import PythonParse
from src.build_scopes import build_scope_graph

test = """
import namespace.abc

class Hello:
    def hello1(self):
        self.a = 1
        pass
        
    def panzer(self):
        pass
"""

build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
