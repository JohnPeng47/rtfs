from pathlib import Path
import os
from typing import Dict
import mimetypes
import fnmatch
import networkx as nx
import json

from llama_index.core import SimpleDirectoryReader
from scope_graph.moatless.epic_split import EpicSplitter
from scope_graph.moatless.settings import IndexSettings

from scope_graph.chunk_resolution.chunk_graph import ChunkGraph


def ingest(repo_path: str) -> ChunkGraph:
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
    chunk_graph = ChunkGraph.from_chunks(Path(repo_path), prepared_nodes)
    print(chunk_graph.to_str())

    return chunk_graph


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
    parser.add_argument(
        "--save", help="Save the output to cluster.json", action="store_true"
    )
    parser.add_argument(
        "--load", help="Load the output from cluster.json", action="store_true"
    )

    repo_path = "tests/repos/cowboy"
    args = parser.parse_args()
    save = args.save
    load = args.load
    if args.loglevel:
        log_level = args.loglevel

    logging.basicConfig(level=log_level, format="%(filename)s: %(message)s")
    print(logging.getLogger().getEffectiveLevel())

    if load:
        with open("cluster.json", "r") as f:
            graph_dict = json.loads(f.read())
            cg = ChunkGraph.from_json(Path(repo_path), graph_dict)

            print(cg.to_str())

            import sys

            sys.exit()

    # ingest("tests/repos/test-import-ref")
    cg = ingest(repo_path)

    if save:
        graph_dict = nx.node_link_data(cg._graph)
        with open("cluster.json", "w") as f:
            f.write(json.dumps(graph_dict))
