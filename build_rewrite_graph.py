import sys

sys.path.append("rtfs_rewrite")

from pathlib import Path
from dataclasses import dataclass
from typing import List

from rtfs_rewrite.ts import cap_ts_queries, TSLangs
from rtfs_rewrite.fs import RepoFs
from rtfs_rewrite.ingest import ingest

from networkx import DiGraph
import networkx as nx
import json


# define a cluster interface to search code over
class Chunk:
    def __init__(self, file_path: Path, id: str):
        self.id = id
        self.file_path = file_path
        self.definitions = []
        self.references = []

    def __str__(self):
        repr = f"[FILE]: {self.file_path.name}\n"
        repr += "".join([f"  [DEFINITIONS]: {d}\n" for d in self.definitions])
        repr += "".join([f"  [REFERENCES]: {r}\n" for r in self.references])
        return repr


def build_repo_graph_v2(repo_path: str) -> None:
    chunks = ingest(repo_path)
    graph = DiGraph()

    all_chunks: List[Chunk] = []
    for chunk in chunks:
        curr_file = Chunk(Path(chunk.metadata["file_path"]), id=chunk.node_id)
        for node, capture_name in cap_ts_queries(
            bytearray(chunk.get_content(), encoding="utf-8"), TSLangs.PYTHON
        ):
            match capture_name:
                case "name.definition.class":
                    curr_file.definitions.append(node.text.decode())

                case "name.definition.function":
                    curr_file.definitions.append(node.text.decode())

                case "name.reference.call":
                    curr_file.references.append(node.text.decode())

        all_chunks.append(curr_file)
        graph.add_node(chunk.node_id)

    # build relation ships
    for c1 in all_chunks:
        for c2 in all_chunks:
            for ref in c1.references:
                if (
                    ref in c2.definitions
                    and c1.id != c2.id
                    and not graph.has_edge(c1.id, c2.id)
                ):
                    graph.add_edge(c1.id, c2.id, ref=ref)

    # Convert the graph to a dictionary
    graph_dict = nx.node_link_data(graph)

    # load into chunk graph and cluster
    print("Graph has been written to 'repo_graph.json'")

    # Write the graph to a JSON file
    with open("repo_graph.json", "w") as json_file:
        json.dump(graph_dict, json_file, indent=2)


if __name__ == "__main__":
    repo_path = sys.argv[1]
    build_repo_graph_v2(repo_path)
