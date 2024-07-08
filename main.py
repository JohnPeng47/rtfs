from src.languages.python.python import PythonParse
from src.build_scopes import build_scope_graph

query, root = PythonParse()._build_query()
build_scope_graph(query, root, 0)
