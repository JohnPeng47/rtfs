from pathlib import Path
import os
from typing import Dict, List
import mimetypes
import fnmatch
import json
import importlib.resources as pkg_resources
import asyncio
from networkx import MultiDiGraph

import cProfile


from llama_index.core import SimpleDirectoryReader

from rtfs.moatless.epic_split import EpicSplitter
from rtfs.moatless.settings import IndexSettings
from rtfs.chunk_resolution.chunk_graph import ChunkGraph

from rtfs.file_resolution.file_graph import FileGraph


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


import time


# untuned implementation could be really expensive
# need to do this at
def construct_edge_series(graph: MultiDiGraph):
    edge_series = []
    visited_edges = set()

    def is_call_to_edge(node, neighbor):
        return any(
            [
                True
                for _, v, attrs in graph.out_edges(node, data=True)
                if v == neighbor and attrs["kind"] == "CallTo"
            ]
        )

    def dfs_edge(current_node, path):
        for neighbor in graph.successors(current_node):
            if is_call_to_edge(current_node, neighbor):
                edge = (current_node, neighbor)
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    new_path = path + [neighbor]

                    # If the neighbor has no other unvisited outgoing 'CallTo' edges, add the path
                    if all(
                        (neighbor, n) in visited_edges
                        or not is_call_to_edge(neighbor, n)
                        for n in graph.successors(neighbor)
                    ):
                        edge_series.append(new_path)
                    else:
                        dfs_edge(neighbor, new_path)

    # Start DFS from each node that has unvisited outgoing 'CallTo' edges
    for node in graph.nodes():
        if any(
            (node, neighbor) not in visited_edges and is_call_to_edge(node, neighbor)
            for neighbor in graph.successors(node)
        ):
            dfs_edge(node, [node])

    return edge_series


async def main(repo_path, saved_graph_path: Path):
    import cProfile
    import pstats
    import io
    from pstats import SortKey
    import time
    from pathlib import Path

    start_time = time.time()
    graph_dict = {}

    # Profile FileGraph.from_repo
    pr = cProfile.Profile()
    pr.enable()
    
    fg = FileGraph.from_repo(Path(repo_path))
    
    pr.disable()
    
    # Print profiling results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(SortKey.CUMULATIVE)
    ps.print_stats(40)  # Print top 20 lines
    print("Profiling results for FileGraph.from_repo:")
    print(s.getvalue())


    # if saved_graph_path.exists():
    #     with open(saved_graph_path, "r") as f:
    #         graph_dict = json.loads(f.read())

    # if graph_dict:
    #     cg = ChunkGraph.from_json(Path(repo_path), graph_dict)
    #     for u, v, attrs in cg._graph.edges(data=True):
    #         if attrs["kind"] == "CallToExport":
    #             print(u, v)

    #     # output = json.dumps(cg.clusters_to_json())
    #     print("hello")
    #     for calls in construct_edge_series(cg._graph):
    #         print(len(calls))

    #     # print(cg.clusters_to_str())

    # else:
    #     cg = ingest(repo_path)
    #     cg.cluster()

    #     # await cg.summarize(user_confirm=True)

    #     graph_dict = cg.to_json()
    #     with open(saved_graph_path, "w") as f:
    #         f.write(json.dumps(graph_dict))

    #     output = json.dumps(cg.clusters_to_json())

    # print(output)

    end_time = time.time()
    print(f"Runtime of the function: {end_time - start_time} seconds")


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
