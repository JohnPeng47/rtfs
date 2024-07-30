from pydantic import BaseModel


class Node(BaseModel):
    id: str


class Edge(BaseModel):
    pass
