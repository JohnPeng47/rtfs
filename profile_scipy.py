from pathlib import Path
import os
from typing import Dict, List
import mimetypes
import fnmatch
import json
import importlib.resources as pkg_resources
import asyncio
from networkx import MultiDiGraph
import click

import cProfile
import pstats
import io
from pstats import SortKey
from pathlib import Path
from functools import wraps
import asyncio

from llama_index.core import SimpleDirectoryReader
from rtfs.moatless.epic_split import EpicSplitter
from rtfs.moatless.settings import IndexSettings
from rtfs.chunk_resolution.chunk_graph import ChunkGraph
from rtfs.summarize.summarize import Summarizer
from rtfs.file_resolution.file_graph import FileGraph
import traceback


def sync_profile_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        result = func(*args, **kwargs)

        pr.disable()

        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(SortKey.CUMULATIVE)
        print("Dumping profiling stats:")
        ps.print_stats(40)  # Restrict to printing 40 lines

        print(f"Profiling results for {func.__name__}:")
        print(s.getvalue())

        return result

    return wrapper


def ingest(repo_path: str, exclude_paths: List[str] = []) -> ChunkGraph:
    def file_metadata_func(file_path: str) -> Dict:
        test_patterns = [
            "**/test/**",
            "**/tests/**",
            "**/test_*.py",
            "**/*_test.py",
        ]
        category = (
            "test"
            if any(fnmatch.fnmatch(file_path, pattern) for pattern in test_patterns)
            else "implementation"
        )

        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_type": mimetypes.guess_type(file_path)[0],
            "category": category,
        }

    reader = SimpleDirectoryReader(
        input_dir=repo_path,
        file_metadata=file_metadata_func,
        filename_as_id=True,
        required_exts=[".py"],  # TODO: Shouldn't be hardcoded and filtered
        recursive=True,
    )

    settings = IndexSettings()
    docs = reader.load_data()

    splitter = EpicSplitter(
        min_chunk_size=settings.min_chunk_size,
        chunk_size=settings.chunk_size,
        hard_token_limit=settings.hard_token_limit,
        max_chunks=settings.max_chunks,
        comment_strategy=settings.comment_strategy,
        repo_path=repo_path,
    )

    prepared_nodes = splitter.get_nodes_from_documents(docs, show_progress=True)
    chunk_graph = ChunkGraph.from_chunks(Path(repo_path), prepared_nodes)

    return chunk_graph


@sync_profile_decorator
def chunk_graph():
    repo_path = "./tests/repos/scipy"
    cg = ingest(repo_path)
    cg.cluster()


chunk_graph()
