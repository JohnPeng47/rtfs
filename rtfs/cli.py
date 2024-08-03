from pathlib import Path
import os
from typing import Dict
import mimetypes
import fnmatch
import json
import importlib.resources as pkg_resources
import asyncio

from llama_index.core import SimpleDirectoryReader

from rtfs.moatless.epic_split import EpicSplitter
from rtfs.moatless.settings import IndexSettings
from rtfs.chunk_resolution.chunk_graph import ChunkGraph


GRAPH_FOLDER = pkg_resources.files("rtfs") / "graphs"


def ingest(repo_path: str) -> ChunkGraph:
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


async def main(repo_path, saved_graph_path: Path):
    graph_dict = {}
    if saved_graph_path.exists():
        with open(saved_graph_path, "r") as f:
            print(f"Loading from saved data .. {saved_graph_path.resolve()}")
            graph_dict = json.loads(f.read())

    if graph_dict:
        cg = ChunkGraph.from_json(Path(repo_path), graph_dict)

        output = cg.to_str_dfs()

    else:
        cg = ingest(repo_path)
        cg.cluster()

        await cg.summarize(user_confirm=True)

        graph_dict = cg.to_json()
        with open(saved_graph_path, "w") as f:
            f.write(json.dumps(graph_dict))

        output = cg.to_str_dfs()

    print(output)


def entrypoint():
    import argparse
    import logging

    log_level = logging.INFO

    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path", help="Path to the repository to ingest")

    args = parser.parse_args()
    repo_path = args.repo_path

    if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        print(f"Path {repo_path} does not exist or is not directory")
        exit()

    logging.basicConfig(level=log_level, format="%(filename)s: %(message)s")

    if not os.path.exists(GRAPH_FOLDER):
        os.makedirs(GRAPH_FOLDER)

    saved_graph_path = Path(GRAPH_FOLDER, Path(repo_path).name + ".json")
    asyncio.run(main(repo_path, saved_graph_path))


if __name__ == "__main__":
    entrypoint()
