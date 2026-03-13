from fastapi import APIRouter, HTTPException
from models.sysarch import PromptRequest, FlowResponse
import json
import re
from groq import Groq
from core.config import settings

router = APIRouter(tags=["sysarch"])
client = Groq(api_key=settings.GROQ_API_KEY)


SYSTEM_PROMPT = """
You are a software architecture expert. When given a description of an application or system,
you must generate a detailed flow diagram represented as JSON.

RULES:
1. Return ONLY valid raw JSON — no markdown, no code fences, no explanation.
2. The JSON must have exactly two top-level keys: "nodes" and "edges".
3. Every node must have: "id" (snake_case string), "label" (short human-readable string), "level" (integer starting from 0).
4. Every edge must have: "from" (source node id), "to" (target node id), "type" ("primary" | "branch" | "loop").
5. Use "primary" for the main sequential flow.
6. Use "branch" for conditional or parallel paths.
7. Use "loop" ONLY when an edge goes BACKWARDS to a lower level node.
8. Levels represent horizontal layers (0 = leftmost/start). Keep related branches on the same level.
9. Every node must be reachable from the start node.
10. Include 10–25 nodes to give good architectural detail.
11. Node ids must be unique and descriptive (e.g. "api_gateway", "auth_service").
12. Do not include any node without at least one edge connecting it.

EXAMPLE OUTPUT FORMAT:
{
  "nodes": [
    { "id": "start", "label": "Entry Point", "level": 0 },
    { "id": "auth", "label": "Auth Service", "level": 1 }
  ],
  "edges": [
    { "from": "start", "to": "auth", "type": "primary" }
  ]
}
"""

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def extract_json(text: str) -> dict:
    """
    Strips any accidental markdown fences and parses JSON.
    Falls back to a regex search if direct parsing fails.
    """
    # Remove ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: find the first { ... } block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("No valid JSON found in model response")


def validate_flow(data: dict) -> dict:
    """
    Basic structural validation + integrity checks on the flow data.
    """
    if "nodes" not in data or "edges" not in data:
        raise ValueError("Response missing 'nodes' or 'edges' keys")

    node_ids = {n["id"] for n in data["nodes"]}

    for node in data["nodes"]:
        for key in ("id", "label", "level"):
            if key not in node:
                raise ValueError(f"Node missing key '{key}': {node}")

    for edge in data["edges"]:
        for key in ("from", "to", "type"):
            if key not in edge:
                raise ValueError(f"Edge missing key '{key}': {edge}")
        if edge["from"] not in node_ids:
            raise ValueError(f"Edge references unknown source: {edge['from']}")
        if edge["to"] not in node_ids:
            raise ValueError(f"Edge references unknown target: {edge['to']}")
        if edge["type"] not in ("primary", "branch", "loop"):
            edge["type"] = "primary"  # safe default

    return data

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.post("/generate-architecture", response_model=FlowResponse)
async def generate_architecture(body: PromptRequest):
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Generate a system architecture flow for: {body.prompt}",
                },
            ],
            temperature=0.4,      # low temp = more consistent JSON
            max_tokens=4096,
            response_format={"type": "json_object"},  # enforce JSON mode
        )

        raw = response.choices[0].message.content
        data = extract_json(raw)
        validated = validate_flow(data)
        return validated

    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq error: {str(e)}")
