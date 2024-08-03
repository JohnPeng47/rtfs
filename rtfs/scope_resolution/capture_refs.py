from rtfs.languages import LANG_PARSER
from rtfs.config import PYTHON_REFS

from typing import List, Dict

from rtfs.utils import TextRange
from rtfs.scope_resolution.reference import Reference


def capture_refs(src_bytes: bytearray, language: str = "python") -> List[Reference]:
    parser = LANG_PARSER[language]
    query, root_node = parser._build_query(src_bytes, PYTHON_REFS)

    refs = []
    for i, (node, capture_name) in enumerate(query.captures(root_node)):
        if capture_name == "local.reference":
            range = TextRange(
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                start_point=node.start_point,
                end_point=node.end_point,
            )
            new_ref = Reference(range, src_bytes)
            refs.append(new_ref)

    return refs
