import networkx as nx
import leidenalg as la
import igraph as ig
from infomap import Infomap

from collections import defaultdict

from logging import getLogger

logger = getLogger(__name__)


def cluster_leiden(digraph: nx.DiGraph):
    # Convert NetworkX DiGraph to igraph Graph
    nodes = list(digraph.nodes())
    edges = list(digraph.edges())

    # Create a mapping from NetworkX node IDs to igraph vertex IDs
    node_id_map = {node: idx for idx, node in enumerate(nodes)}

    # Initialize an igraph Graph
    ig_graph = ig.Graph(directed=True)

    # Add vertices to the igraph Graph
    ig_graph.add_vertices(len(nodes))

    # Add original node IDs as vertex attributes
    ig_graph.vs["name"] = nodes

    # Add edges to the igraph Graph using the mapped vertex IDs
    ig_edges = [(node_id_map[edge[0]], node_id_map[edge[1]]) for edge in edges]
    ig_graph.add_edges(ig_edges)

    # Run Leiden clustering
    partition = la.find_partition(ig_graph, la.ModularityVertexPartition)

    # Extract the clusters using original node IDs
    node2clusters = {}
    cluster2nodes = defaultdict(list)

    for idx, cluster in enumerate(partition):
        for node in cluster:
            original_node_id = ig_graph.vs[node]["name"]
            node2clusters[original_node_id] = idx
            cluster2nodes[idx].append(original_node_id)

    return node2clusters, cluster2nodes


def cluster_infomap(digraph: nx.DiGraph):
    # Initialize Infomap
    infomap = Infomap("--two-level")

    # Create a mapping from NetworkX node IDs to integer IDs
    node_id_map = {node: idx for idx, node in enumerate(digraph.nodes())}
    reverse_node_id_map = {idx: node for node, idx in node_id_map.items()}

    # Add nodes and edges to Infomap using integer IDs
    for edge in digraph.edges():
        infomap.addLink(node_id_map[edge[0]], node_id_map[edge[1]])

    # Run Infomap clustering
    infomap.run()

    # Extract the clusters using original node IDs
    node2clusters = {}
    cluster2nodes = defaultdict(list)

    for node in infomap.iterTree():
        if node.isLeaf:
            original_node_id = reverse_node_id_map[node.physicalId]

            node2clusters[original_node_id] = node.moduleIndex()
            cluster2nodes[node.moduleIndex()].append(original_node_id)

    return node2clusters, cluster2nodes
