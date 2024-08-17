import networkx as nx
from infomap import Infomap
import yaml
from dataclasses import dataclass, field
from typing import Dict, List
import time

from rtfs.models import OpenAIModel

from logging import getLogger

logger = getLogger(__name__)


def cluster_infomap(digraph: nx.DiGraph) -> Dict[int, List]:
    # Initialize Infomap
    infomap = Infomap("--seed 42", silent=True)

    # Create a mapping from NetworkX node IDs to integer IDs
    node_id_map = {node: idx for idx, node in enumerate(digraph.nodes())}
    reverse_node_id_map = {idx: node for node, idx in node_id_map.items()}

    # Add nodes and edges to Infomap using integer IDs
    for edge in digraph.edges():
        infomap.addLink(node_id_map[edge[0]], node_id_map[edge[1]])

    infomap.run()
    # Run Infomap clustering

    cluster_dict: Dict[int, List] = {}
    # node_id, path
    # 1 (1, 2, 2)
    for node, levels in infomap.get_multilevel_modules().items():
        node_id = reverse_node_id_map[node]
        cluster_dict[node_id] = [lvl for lvl in levels]

    # replace leaf nodes with their original id

    return cluster_dict
