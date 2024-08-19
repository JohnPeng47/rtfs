import yaml
from typing import Dict, List
import random

from .chunk_graph import ChunkGraph
from .graph import ClusterNode, NodeKind, SummarizedChunk, ClusterEdgeKind, ClusterEdge

from rtfs.utils import dfs_json, VerboseSafeDumper
from rtfs.models import OpenAIModel


# SUMMARY_OG = """
# The following chunks of code are grouped into the same feature.
# I want you to respond with a yaml object that contains the following fields:
# - first come up with a descriptive title that best captures the role that these chunks of code
# play in the overall codebase.
# - next, write a single paragraph summary of the chunks of code
# - finally, take a list of key variables/functions/classes from the code

# Your yaml should take the following format:

# title: str
# summary: str
# key_variables: List[str]

# Here is the code:
# {code}
# """

SUMMARY_FIRST_PASS = """
The following chunks of code are grouped into the same feature.
I want you to respond with a yaml object that contains the following fields: 
- first come up with a descriptive title that best captures the role that these chunks of code
play in the overall codebase. 
- next, write a short concise but descriptive summary of the chunks, thats 1-2 sentences long
- finally, take a list 4 of important functions/classes as key_variables

Your yaml should take the following format:

title: str
summary: str
key_variables: List[str]

Here is the code:
{code}
"""

REORGANIZE_CLUSTERS = """
You are given a following a set of clusters that each represent a hierarchal grouping
of functionalities in a codebase. There may be a better way of organizing these clusters.
I want you to carefully think through each feature grouping, and then reorganize the clusters
accordingly. Here are some more precise instructions:

1. Carefully read through the entire list of features and functionalities.
2. Place each feature or functionality under the most appropriate category or subcategory.
3. Within each category and subcategory, order the features in a logical manner (e.g., from most basic to most advanced, or in order of typical user workflow).
4. You can remove/add clusters ONLY IF they have no children

Your generated output should be a yaml object that only contains title and children fields as in the following format:

title: str
children: 
    - title: str
        children:
title: str
children:
...

{cluster_yaml}
"""


def get_cluster_id():
    return random.randint(1, 10000000)


class LLMException(Exception):
    pass


class Summarizer:
    def __init__(self):
        self._model = OpenAIModel()

    # TODO: when parallelizing this need to make sure that order
    # of the clusters is maintained during summary generation
    # can only parallelize one whole depth level at a time
    def iterate_clusters_with_text(self, cg: ChunkGraph):
        for cluster in [
            node
            for node, data in cg._graph.nodes(data=True)
            if data["kind"] == NodeKind.Cluster
        ]:
            child_content = "\n".join(
                [
                    cg.get_node(c).get_content()
                    for c in cg.children(cluster)
                    if cg.get_node(c).kind == NodeKind.Chunk
                    or cg.get_node(c).kind == NodeKind.Cluster
                ]
            )
            yield (cluster, child_content)

    def clusters_to_str(self):
        INDENT_SYM = lambda d: "-" * d + " " if d > 0 else ""

        clusters_json = self.clusters_to_json()
        result = ""

        for cluster_json in clusters_json:
            for node, depth in dfs_json(cluster_json):
                indent = "  " * depth
                result += f"{INDENT_SYM(depth)}{node['title']}\n"
                result += f"{indent}Keywords: {node['key_variables']}\n"
                result += f"{indent}Summary: {node['summary']}\n"
                for chunk in node["chunks"]:
                    result += f"{indent}  ChunkNode: {chunk['id']}\n"

        return result

    # TODO: need some way handling cases where the code is too long
    def clusters_to_yaml(self, cg: ChunkGraph):
        num_parent_clusters = 0
        num_child_clusters = 0

        clusters_json = cg.clusters_to_json()
        clusters_dict = []

        # count the number of parent and child clusters
        for cluster_json in clusters_json:
            for node, depth in dfs_json(cluster_json):
                if node["children"] == []:
                    num_child_clusters += 1
                else:
                    num_parent_clusters += 1

                del node["chunks"]
                del node["key_variables"]

                clusters_dict.append(node)

        return (
            yaml.dump(
                clusters_dict,
                Dumper=VerboseSafeDumper,
                # default_flow_style=False,
                sort_keys=False,
            ),
            num_parent_clusters,
            num_child_clusters,
        )

    async def reorg_cluster(self, cg: ChunkGraph) -> Dict[int, SummarizedChunk]:
        """
        Reorganizes the clusters generated from infomap
        """
        cluster_str, old_parent_num, old_child_num = self.clusters_to_yaml(cg)
        prompt = REORGANIZE_CLUSTERS.format(cluster_yaml=cluster_str)

        res = await self._model.query_yaml(prompt)

        num_cluster_nodes = sum(
            1 for node, data in cg._graph.nodes(data=True) if data["kind"] == "Cluster"
        )
        print(f"Number of cluster nodes in the graph: {num_cluster_nodes}")

        new_parent_num = 0
        new_child_num = 0

        def walk_reorg(cluster_yaml, parent_id=None):
            nonlocal new_parent_num, new_child_num

            if type(cluster_yaml) is list:
                [walk_reorg(child, parent_id) for child in cluster_yaml]
                return

            cluster_node = cg.find_cluster_node_by_title(cluster_yaml["title"])
            # new cluster node
            if not cluster_node:
                cluster_node = ClusterNode(
                    id=get_cluster_id(),
                    title=cluster_yaml["title"],
                )
                cg.add_node(cluster_node)

            # changed child/cluster relation
            if parent_id and not cg._graph.has_edge(cluster_node.id, parent_id):
                # Remove any existing edges from cluster_node.id
                edges_to_remove = list(cg._graph.out_edges(cluster_node.id))
                for edge in edges_to_remove:
                    cg._graph.remove_edge(*edge)

                edge = ClusterEdge(kind=ClusterEdgeKind.ClusterToCluster)
                cg.add_edge(parent_id, cluster_node.id, edge)

            if cluster_yaml["children"]:
                new_parent_num += 1
                for child in cluster_yaml["children"]:
                    # walk_reorg(child, parent_id=None)
                    walk_reorg(child, parent_id=cluster_node.id)
            else:
                new_child_num += 1

        walk_reorg(res)

        print(new_parent_num, new_child_num)
        print(old_parent_num, old_child_num)
        num_cluster_nodes = sum(
            1 for node, data in cg._graph.nodes(data=True) if data["kind"] == "Cluster"
        )
        print(f"Number of cluster nodes in the graph: {num_cluster_nodes}")

        return res

    def user_confirm(self, cg: ChunkGraph) -> bool:
        agg_chunks = ""
        for _, child_content in self.iterate_clusters_with_text(cg):
            agg_chunks += child_content

        tokens, cost = self._model.calc_input_cost(agg_chunks)
        user_input = input(
            f"The summarization will cost ${cost} and use {tokens} tokens. Do you want to proceed? (yes/no): "
        )
        if user_input.lower() != "yes":
            print("Aborted.")
            return False

        return True

    # TODO: parallelize this
    async def summarize(
        self, cg: ChunkGraph, user_confirm: bool = False, test_run: bool = False
    ):
        if user_confirm and not self.user_confirm(cg):
            return

        ### first pass
        limit = 2 if test_run else float("inf")
        for cluster_id, child_content in self.iterate_clusters_with_text(cg):
            try:
                prompt = SUMMARY_FIRST_PASS.format(code=child_content)
                summary_data = await self._model.query_yaml(prompt)
                # type-check llm response
                summary_data = SummarizedChunk(**summary_data)
            except LLMException:
                continue

            print("updating node: ", cluster_id, "with summary: ", summary_data)
            cluster_node = ClusterNode(id=cluster_id, **summary_data.to_dict())
            cg.update_node(cluster_node)

            limit -= 1
            if limit < 0:
                break

        ### second pass
        # self.reorg_cluster(cg)
