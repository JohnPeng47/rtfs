from rtfs.chunk_resolution.chunk_graph import ChunkGraph
from conftest import chunk_graph, chunk_nodes, CHUNK_GRAPH
import os

import pytest


@pytest.mark.parametrize(
    "chunk_nodes", ["tests/repos/cowboy-server"], indirect=["chunk_nodes"]
)
@pytest.mark.parametrize(
    "chunk_graph", ["tests/repos/cowboy-server"], indirect=["chunk_graph"]
)
def test_confirm_imports(chunk_graph: ChunkGraph):
    chunk_graph.cluster()

    print(chunk_graph.to_str_cluster())
    assert CHUNK_GRAPH == chunk_graph.to_str_cluster()
