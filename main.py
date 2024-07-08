from src.languages.python.python import PythonParse
from src.build_scopes import build_scope_graph

test = """
import abc

class Hello:
    string: a = 1
    helloworld = 2    

    def hello1(self):
        pass
        
    def panzer():
        pass
"""

query, root = PythonParse()._build_query(bytearray(test, encoding="utf-8"))
build_scope_graph(query, root, 0)
