LANGUAGE = "python"

FILE_GLOB_ENDING = {"python": "*.py"}

SUPPORTED_LANGS = {"python": "python"}

NAMESPACE_DELIMETERS = {"python": "."}

SYS_MODULES_LIST = "src/languages/{lang}/sys_modules.json".format(lang=LANGUAGE)

THIRD_PARTY_MODULES_LIST = "src/languages/{lang}/third_party_modules.json".format(
    lang=LANGUAGE
)
