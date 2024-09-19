import yaml
from typing import Dict, List
import random

from ..chunk_resolution.chunk_graph import ChunkGraph
from ..chunk_resolution.graph import (
    ClusterNode,
    NodeKind,
    SummarizedChunk,
    ClusterEdgeKind,
    ClusterEdge,
)

from rtfs.graph import CodeGraph
from rtfs.utils import dfs_json, VerboseSafeDumper
from rtfs.models import OpenAIModel

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
You are given a following a set of clusters that encapsulate different features in the codebase. Take these clusters
and group them into logical categories, then come up with a name for each category

Here are some more precise instructions:
1. Carefully read through the entire list of features and functionalities.
2. The categories must be mutually exclusive and collectively exhaustive.
3. Place each feature or functionality under the most appropriate category
4. Each category should not have less than 2 children clusters

Your generated output should only contain the title of the your created categories and their list of children.
Return your output in a yaml object, with the following format:

- category: str
    children: []
- category: str
    children: []
- category: str
    children: []
...

{cluster_yaml}
"""


def get_cluster_id():
    return random.randint(1, 10000000)


class LLMException(Exception):
    pass


class Summarizer:
    accepted_nodes: List[str] = ["ClusterNode", "ChunkNode"]

    def __init__(self, graph: CodeGraph):
        self._model = OpenAIModel()
        self._graph = graph

        for node_type in self._graph.node_types:
            if node_type.__name__ not in self.accepted_nodes:
                raise ValueError(f"Unsupported node type: {node_type.__name__}")

    # TODO: when parallelizing this need to make sure that order
    # of the clusters is maintained during summary generation
    # can only parallelize one whole depth level at a time
    def iterate_clusters_with_text(self, cg: ChunkGraph):
        for cluster in [
            node
            for node, data in self._graph.nodes(data=True)
            if data["kind"] == NodeKind.Cluster
        ]:
            child_content = "\n".join(
                [
                    self._graph.get_node(c).get_content()
                    for c in self._graph.children(cluster)
                    if self._graph.get_node(c).kind == NodeKind.Chunk
                    or self._graph.get_node(c).kind == NodeKind.Cluster
                ]
            )
            yield (cluster, child_content)

    # TODO: move clusters_to_json out of CG
    # TODO: need some way handling cases where the code is too long
    def clusters_to_yaml(self, cg: ChunkGraph):
        clusters_json = cg.clusters_to_json()
        for cluster in clusters_json:
            del cluster["chunks"]
            del cluster["key_variables"]

        return yaml.dump(
            clusters_json,
            Dumper=VerboseSafeDumper,
            # default_flow_style=False,
            sort_keys=False,
        ), len(clusters_json)

    async def gen_categories(
        self, cg: ChunkGraph, retries: int = 3
    ) -> Dict[int, SummarizedChunk]:
        """
        Generates another level of clusters from existing clusters
        """
        for attempt in range(retries):
            try:
                cluster_str, num_clusters = self.clusters_to_yaml(self._graph)
                prompt = REORGANIZE_CLUSTERS.format(cluster_yaml=cluster_str)
                yaml_res = await self._model.query_yaml(prompt)

                num_generated_nodes = 0
                for category in yaml_res:
                    cluster_node = ClusterNode(
                        id=get_cluster_id(),
                        title=category["category"],
                        kind=NodeKind.Cluster,
                    )
                    self._graph.add_node(cluster_node)
                    for child in category["children"]:
                        child_node = self._graph.find_cluster_node_by_title(child)
                        self._graph.add_edge(
                            child_node.id,
                            cluster_node.id,
                            ClusterEdge(
                                kind=ClusterEdgeKind.ClusterToCluster,
                            ),
                        )

                        num_generated_nodes += 1

                if num_clusters != num_generated_nodes:
                    raise Exception(
                        "Number of generated nodes does not match number of clusters"
                    )

                break
            except Exception as e:
                if attempt < retries - 1:
                    print(
                        f"Error in generating categories (attempt {attempt + 1}/{retries}): {e}"
                    )
                else:
                    raise LLMException("Exception generating categories")

    def user_confirm(self, cg: ChunkGraph) -> bool:
        agg_chunks = ""
        for _, child_content in self.iterate_clusters_with_text(self._graph):
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
        if user_confirm and not self.user_confirm(self._graph):
            return

        ### first pass
        limit = 2 if test_run else float("inf")
        for cluster_id, child_content in self.iterate_clusters_with_text(self._graph):
            try:
                prompt = SUMMARY_FIRST_PASS.format(code=child_content)
                summary_data = await self._model.query_yaml(prompt)
                # type-check llm response
                summary_data = SummarizedChunk(**summary_data)
            except LLMException:
                continue

            print("updating node: ", cluster_id, "with summary: ", summary_data)
            cluster_node = ClusterNode(id=cluster_id, **summary_data.to_dict())
            self._graph.update_node(cluster_node)

            limit -= 1
            if limit < 0:
                break
