from tree_sitter import Language, Parser

PYTHONTS_LIB = "src/languages/python/libs/my-python.so"
PYTHON_SCM = "src/languages/python/python.scm"


class PythonParse:
    @classmethod
    def _build_query(cls, file_content: bytearray):
        query_file = open(PYTHON_SCM, "rb").read()

        PY_LANGUAGE = Language(PYTHONTS_LIB, "python")
        parser = Parser()
        parser.set_language(PY_LANGUAGE)

        root = parser.parse(file_content).root_node
        query = PY_LANGUAGE.query(query_file)

        return query, root
