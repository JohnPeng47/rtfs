LANGUAGE = "python"

PYTHONTS_LIB = "scope_graph/languages/python/libs/my-python.so"
PYTHON_SCM = "scope_graph/languages/python/python.scm"

FILE_GLOB_ENDING = {"python": ".py"}

SUPPORTED_LANGS = {"python": "python"}

NAMESPACE_DELIMETERS = {"python": "."}

SYS_MODULES_LIST = "scope_graph/languages/{lang}/sys_modules.json".format(lang=LANGUAGE)

THIRD_PARTY_MODULES_LIST = (
    "scope_graph/languages/{lang}/third_party_modules.json".format(lang=LANGUAGE)
)
