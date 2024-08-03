import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from rtfs.config import PYTHON_SCM, PYTHONTS_LIB


class PythonParse:

    @classmethod
    def _build_query(cls, file_content: bytearray, query_file: str):
        query_file = open(PYTHON_SCM, "rb").read()

        PY_LANGUAGE = Language(tspython.language())

        parser = Parser()
        parser.set_language(PY_LANGUAGE)

        root = parser.parse(file_content).root_node
        query = PY_LANGUAGE.query(query_file)

        return query, root
