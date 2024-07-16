from pathlib import Path
import os
from typing import Dict
import mimetypes
import fnmatch

from llama_index.core import SimpleDirectoryReader
from scope_graph.moatless.epic_split import EpicSplitter
from scope_graph.moatless.settings import IndexSettings

from scope_graph.chunk_resolution.chunk_graph import ChunkGraph


def ingest(repo_path: str):
    def file_metadata_func(file_path: str) -> Dict:
        file_path = file_path.replace(repo_path, "")
        if file_path.startswith("/"):
            file_path = file_path[1:]

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
    chunk_graph = ChunkGraph(Path(repo_path), prepared_nodes)


if __name__ == "__main__":
    import argparse
    import logging

    log_level = logging.INFO

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        help="Print lots of debugging statements",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
    )

    args = parser.parse_args()
    if args.loglevel:
        log_level = args.loglevel

    logging.basicConfig(level=log_level, format="%(filename)s: %(message)s")
    print(logging.getLogger().getEffectiveLevel())

    ingest("tests/repos/small_repo")
