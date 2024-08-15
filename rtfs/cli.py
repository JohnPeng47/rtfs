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
from rtfs.file_resolution.file_graph import FileGraph
import traceback

GRAPH_FOLDER = pkg_resources.files("rtfs") / "graphs"

def profile_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        result = await func(*args, **kwargs)

        pr.disable()

        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(SortKey.CUMULATIVE)
        ps.print_stats(40)  # Print top 40 lines
        print(f"Profiling results for {func.__name__}:")
        print(s.getvalue())

        return result

    return wrapper


@profile_decorator
async def profiled_main(repo_path, saved_graph_path: Path):
    fg = FileGraph.from_repo(Path(repo_path))

    return fg  # or whatever you want to return from main

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

@click.group()
def cli():
    """RTFS CLI tool for repository analysis."""
    pass


@cli.command()
@click.argument(
    "repo_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--saved-graph-path", type=click.Path(), default=None)
def file_graph(repo_path, saved_graph_path):
    """Generate a FileGraph from the repository."""
    fg = FileGraph.from_repo(Path(repo_path))
    click.echo("FileGraph generated successfully.")


@cli.command()
@click.argument(
    "repo_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--test-run", is_flag=True)
@click.option("--output-format", type=click.Choice(["str", "json"]), default="str")
@click.option("--output-file", type=click.Path(), default=None)
def chunk_graph(
    repo_path, test_run, output_format, output_file
):  # Modified line
    """Generate and manipulate ChunkGraph."""

    saved_graph_path = Path(GRAPH_FOLDER, Path(repo_path).name + ".json")
    if saved_graph_path.exists():
        with open(saved_graph_path, "r") as f:
            graph_dict = json.loads(f.read())

        print("Loading graph from saved file")
        cg = ChunkGraph.from_json(Path(repo_path), graph_dict)
    else:
        cg = ingest(repo_path)
        cg.cluster()
        asyncio.run(cg.summarize(user_confirm=True, test_run=test_run))

    if output_format == "str":
        click.echo(cg.clusters_to_str())
    elif output_format == "json":
        clusters_json = cg.clusters_to_json()
        if output_file:
            with open(output_file, "w") as f:
                json.dump(clusters_json, f, indent=2)
            click.echo(f"Clusters JSON written to {output_file}")
        else:
            click.echo(json.dumps(clusters_json, indent=2))

    click.echo("ChunkGraph generated and processed successfully.")


if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {e}")
        traceback.print_exc()
        raise e
