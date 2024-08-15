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


class LLMException(Exception):
    pass


@dataclass
class SummarizedChunk:
    title: str = ""
    summary: str = ""
    key_variables: List[str] = field(default_factory=list)


def summarize_chunk_text(cluster, model: OpenAIModel) -> SummarizedChunk:
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
        # reason for exponential backoff is, I think 
        # >>> [1.5**b for b in a]
        # [1.5, 2.25, 3.375, 5.0625, 7.59375]

        back_off = 1.5
        # Retry logic for yaml parsing
        for attempt in range(1, 6):
            try:
                response = await model.query(prompt.format(code=cluster))
                yaml_content = response.split("```yaml")[1].split("```")[0].strip()

                return SummarizedChunk(**yaml.safe_load(yaml_content))
            # TODO: check if this fails 3 times only or not at all
            except Exception as e:
                print("Failed attempt : ", attempt)
                
                time.sleep(back_off ** attempt)
                if attempt > 5:
                    raise LLMException("Failed to parse YAML after 5 attempts") from e

    return query_model(cluster)
