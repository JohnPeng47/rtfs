import networkx as nx
from infomap import Infomap
import yaml
from dataclasses import dataclass, field
from typing import Dict, List
import time

from rtfs.models import OpenAIModel

from logging import getLogger

logger = getLogger(__name__)


def cluster_infomap(digraph: nx.DiGraph) -> Dict[str, int]:
    # Initialize Infomap
    infomap = Infomap("--seed 42 --two-level", silent=True)

    # Create a mapping from NetworkX node IDs to integer IDs
    node_id_map = {node: idx for idx, node in enumerate(digraph.nodes())}
    reverse_node_id_map = {idx: node for node, idx in node_id_map.items()}

    # Add nodes and edges to Infomap using integer IDs
    for edge in digraph.edges():
        infomap.addLink(node_id_map[edge[0]], node_id_map[edge[1]])

    # Run Infomap clustering
    infomap.run()

    # Create the {codechunk: cluster} mapping
    cluster_dict: Dict[str, int] = {}
    for node, modules in infomap.get_multilevel_modules().items():
        node_id = reverse_node_id_map[node]
        # We use the last level as the cluster ID
        cluster_dict[node_id] = modules[-1]

    return cluster_dict
