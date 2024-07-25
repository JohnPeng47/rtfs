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


GRAPH_FOLDER = "graphs"


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


def get_node2cluster(chunk2clusters):
    return {
        self.get_node(node_id): cluster for node_id, cluster in chunk2clusters.items()
    }


def get_cluster2node(cluster2chunks):
    return {
        cluster: [self.get_node(node_id) for node_id in node_ids]
        for cluster, node_ids in cluster2chunks.items()
    }


def main(repo_path, saved_graph_path, load: bool = False, save: bool = False):
    import time

    start_time = time.time()

    if load:
        with open(saved_graph_path, "r") as f:
            graph_dict = json.loads(f.read())
            cg = ChunkGraph.from_json(Path(repo_path), graph_dict)

            chunk2cluster, cluster2chunk = cg.cluster()
            print(json.dumps(chunk2cluster, indent=4))

            print(f"Execution time: {time.time() - start_time:.2f} seconds")
            exit()

    cg = ingest(repo_path)
    if save:
        print("Saving graph to disk")
        graph_dict = nx.node_link_data(cg._graph)
        with open(saved_graph_path, "w") as f:
            f.write(json.dumps(graph_dict))

    print(f"Execution time: {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
    import argparse
    import logging

    log_level = logging.INFO

    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path", help="Path to the repository to ingest")
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

    args = parser.parse_args()
    repo_path = args.repo_path
    if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        print(f"Path {repo_path} does not exist or is not directory")
        exit()

    save = args.save
    load = args.load
    if args.loglevel:
        log_level = args.loglevel

    logging.basicConfig(level=log_level, format="%(filename)s: %(message)s")

    saved_graph_path = os.path.join(GRAPH_FOLDER, Path(repo_path).name + ".json")
    main(repo_path, saved_graph_path, load=load, save=save)
