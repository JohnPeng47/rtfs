import networkx as nx
import leidenalg as la
import igraph as ig
from infomap import Infomap
import yaml
from collections import defaultdict
from typing import Dict, List

from models import OpenAIModel

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


def cluster_infomap(digraph: nx.DiGraph) -> Dict[int, List]:
    # Initialize Infomap
    infomap = Infomap("--seed 42")

    # Create a mapping from NetworkX node IDs to integer IDs
    node_id_map = {node: idx for idx, node in enumerate(digraph.nodes())}
    reverse_node_id_map = {idx: node for node, idx in node_id_map.items()}

    # Add nodes and edges to Infomap using integer IDs
    for edge in digraph.edges():
        infomap.addLink(node_id_map[edge[0]], node_id_map[edge[1]])

    # Run Infomap clustering
    infomap.run()

    cluster_dict: Dict[int, List] = {}
    # node_id, path
    # 1 (1, 2, 2)
    for node, levels in infomap.get_multilevel_modules().items():
        node_id = reverse_node_id_map[node]
        cluster_dict[node_id] = [lvl for lvl in levels]

    # replace leaf nodes with their original id

    return cluster_dict


def cluster_infomap_multilevel(digraph: nx.DiGraph, num_trials: int = 10):
    # Initialize Infomap
    infomap = Infomap(f"--seed 42")

    # Create a mapping from NetworkX node IDs to integer IDs
    node_id_map = {node: idx for idx, node in enumerate(digraph.nodes())}
    reverse_node_id_map = {idx: node for node, idx in node_id_map.items()}

    # Add nodes and edges to Infomap using integer IDs
    for edge in digraph.edges():
        infomap.addLink(node_id_map[edge[0]], node_id_map[edge[1]])

    # Run Infomap clustering
    infomap.run()

    return infomap

    # # Extract the multi-level clusters using original node IDs
    # node2clusters = defaultdict(list)
    # cluster2nodes = defaultdict(lambda: defaultdict(list))

    # for node in infomap.iterTree():
    #     if node.isLeaf:
    #         original_node_id = reverse_node_id_map[node.physicalId]

    #         # Get all levels of clustering for this node
    #         path = []
    #         current = node
    #         while current.parent is not None:
    #             path.append(current.moduleIndex())
    #             current = current.parent
    #         path.reverse()  # Reverse to get top-level first

    #         # Store the full path for each node
    #         node2clusters[original_node_id] = path

    #         # Store nodes for each cluster at each level
    #         for level, cluster_id in enumerate(path):
    #             cluster2nodes[level][cluster_id].append(original_node_id)

    # return node2clusters, cluster2nodes


class LLMException(Exception):
    pass


def summarize_cluster(cluster, model: OpenAIModel):
    prompt = """
The following chunks of code are grouped into the same feature.
I want you to respond with a yaml object that contains the following fields: 
- first come up with a descriptive title that best captures the role that these chunks of code
play in the overall codebase. 
- next, write a single paragraph summary of the chunks of code
- finally, take a list of key variables/functions/classes from the code

Your yaml should take the following format:

title: str
summary: str
key_variables: List[str]

Here is the code:
{code}
    """

    async def query_model(cluster):
        response = await model.query(prompt.format(code=cluster))

        # Extract the yaml content from the response
        yaml_content = response.split("```yaml")[1].split("```")[0].strip()

        # Retry logic for yaml parsing
        for attempt in range(3):
            try:
                return yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                if attempt < 2:
                    print(f"YAML parsing failed on attempt {attempt + 1}, retrying...")
                else:
                    raise LLMException("Failed to parse YAML after 3 attempts") from e

    return query_model(cluster)


async def gen_cluster_summaries(cluster2nodes, model: OpenAIModel):
    sum_chunks = []
    for cluster, nodes in list(cluster2nodes.items()):
        if len(nodes) <= 10:
            chunk = "\n".join(
                [node.metadata.file_path + "\n" + node.content for node in nodes]
            )

            try:
                sum_chunk = await summarize_cluster(chunk, model)
                sum_chunk["cluster"] = cluster
                sum_chunk["chunk_ids"] = [node.og_id for node in nodes]

                sum_chunks.append(sum_chunk)

            except LLMException as e:
                print(f"Failed to summarize cluster {cluster}:")
                continue

    return sum_chunks
