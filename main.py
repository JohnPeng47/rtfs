from scope_graph.build_scopes import build_scope_graph

from scope_graph.repo_resolution.repo_graph import RepoGraph
from pathlib import Path


## Failing tests
# Dotted assignment/ref
# test = """
# h.a = 1
# h.a = h.b

# def func1():
#     a = b
#     b = 2
# """

test = """
import re
import time
from typing import Sequence, List, Optional, Any, Callable
from hashlib import sha256
from enum import Enum

from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks import CallbackManager
from llama_index.core.node_parser import NodeParser, TextSplitter, TokenTextSplitter
from llama_index.core.node_parser.node_utils import logger
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.utils import get_tqdm_iterable, get_tokenizer

from scope_graph.moatless.codeblocks import (
    PathTree,
    CodeBlock,
    CodeBlockType,
)
from scope_graph.moatless.parser.python import PythonParser
from scope_graph.moatless.settings import CommentStrategy


class CodeNode(TextNode):

    # Skip start and end line in metadata to try to lower the number of changes and triggers of new embeddings.
    @property
    def hash(self):
        metadata = self.metadata.copy()
        metadata.pop("start_line", None)
        metadata.pop("end_line", None)
        doc_identity = str(self.text) + str(metadata)
        return str(sha256(doc_identity.encode("utf-8", "surrogatepass")).hexdigest())


CodeBlockChunk = List[CodeBlock]


def count_chunk_tokens(chunk: CodeBlockChunk) -> int:
    return sum([block.tokens for block in chunk])


def count_parent_tokens(codeblock: CodeBlock) -> int:
    tokens = codeblock.tokens
    if codeblock.parent:
        tokens += codeblock.parent.tokens
    return tokens


SPLIT_BLOCK_TYPES = [
    CodeBlockType.FUNCTION,
    CodeBlockType.CLASS,
    CodeBlockType.TEST_SUITE,
    CodeBlockType.TEST_CASE,
    CodeBlockType.MODULE,
]


class EpicSplitter(NodeParser):

"""

# scope_graph = build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
# print(scope_graph.to_str())

# print(scope_graph.to_str())
repo_graph = RepoGraph(Path("tests/repos/small_repo"))
repo_graph.print_missing_imports()
print(repo_graph.to_str())
