import networkx as nx
import leidenalg as la
import igraph as ig

from collections import defaultdict


def cluster(digraph: nx.DiGraph):
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
    chunk2clusters = {}
    cluster2chunks = defaultdict(list)

    for idx, cluster in enumerate(partition):
        for node in cluster:
            original_node_id = ig_graph.vs[node]["name"]
            chunk2clusters[original_node_id] = idx
            cluster2chunks[idx].append(original_node_id)

    return chunk2clusters, cluster2chunks
