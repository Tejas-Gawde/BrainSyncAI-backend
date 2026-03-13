from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class NodeSchema(BaseModel):
    id: str
    label: str
    level: int

class EdgeSchema(BaseModel):
    from_node: str
    to_node: str
    type: str  # "primary" | "branch" | "loop"

    class Config:
        populate_by_name = True
        fields = {"from_node": "from", "to_node": "to"}

class FlowResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]
