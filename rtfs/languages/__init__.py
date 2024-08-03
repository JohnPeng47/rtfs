from .python import PythonParse

# TODO: when we have to implement a third one of these things,
# build a factory class to do it properly
LANG_PARSER = {"python": PythonParse}
