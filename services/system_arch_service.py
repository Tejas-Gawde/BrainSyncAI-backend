import re

def extract_json(text: str) -> str:
    """
    Strips markdown fences and extracts the raw JSON string.
    Mirrors the extractJson() function from the Node.js version.
    """
    # Remove ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()

    # If it starts with { it's probably clean already
    if cleaned.startswith("{"):
        return cleaned

    # Last resort: find the outermost { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return match.group()

    raise ValueError("No valid JSON object found in model response")


def validate_flowchart(data: dict) -> bool:
    """
    Mirrors the validateFlowChart() function from the Node.js version.
    Checks that nodes have id/label and edges have from/to.
    """
    if not isinstance(data, dict):
        return False
    if "nodes" not in data or "edges" not in data:
        return False
    if not isinstance(data["nodes"], list) or not isinstance(data["edges"], list):
        return False

    # Validate nodes
    node_ids = set()
    for node in data["nodes"]:
        if not isinstance(node, dict):
            return False
        if "id" not in node or "label" not in node:
            return False
        node_ids.add(node["id"])

    # Validate edges
    for edge in data["edges"]:
        if not isinstance(edge, dict):
            return False
        if "from" not in edge or "to" not in edge:
            return False
        # Ensure edge references existing nodes
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            return False

    return True


def assign_levels(data: dict) -> dict:
    """
    If the model forgot to include 'level' on nodes, compute them
    via BFS from the first node so the frontend always has level data.
    """
    node_ids = [n["id"] for n in data["nodes"]]
    if not node_ids:
        return data

    # Check if levels are already present and valid
    if all("level" in n and isinstance(n["level"], int) for n in data["nodes"]):
        return data

    # Build adjacency list
    adj: dict[str, list[str]] = {nid: [] for nid in node_ids}
    for edge in data["edges"]:
        src, tgt = edge["from"], edge["to"]
        if src in adj:
            adj[src].append(tgt)

    # BFS from root node
    levels: dict[str, int] = {}
    queue = [node_ids[0]]
    levels[node_ids[0]] = 0

    while queue:
        current = queue.pop(0)
        for neighbor in adj.get(current, []):
            if neighbor not in levels:
                levels[neighbor] = levels[current] + 1
                queue.append(neighbor)

    # Assign levels — default 0 for any unreachable nodes
    for node in data["nodes"]:
        node["level"] = levels.get(node["id"], 0)

    return data
