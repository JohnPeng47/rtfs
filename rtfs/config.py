import importlib.resources as pkg_resources

LANGUAGE = "python"
LANG_MODULE = pkg_resources.files(f"rtfs") / "languages" / LANGUAGE

PYTHONTS_LIB = LANG_MODULE / "libs/my-python.so"
PYTHON_SCM = LANG_MODULE / "python.scm"
PYTHON_REFS = LANG_MODULE / "python_refs.scm"

FILE_GLOB_ENDING = {"python": ".py"}

SUPPORTED_LANGS = {"python": "python"}

NAMESPACE_DELIMETERS = {"python": "."}

SYS_MODULES_LIST = LANG_MODULE / "sys_modules.json"

THIRD_PARTY_MODULES_LIST = LANG_MODULE / "third_party_modules.json"
