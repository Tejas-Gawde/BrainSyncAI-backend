from bson import ObjectId
from datetime import datetime
from db.mongodb import get_db

def _now():
    return datetime.utcnow()


async def create_message(playground_id: str, sender_id: str | None, content: str, sender_username: str | None = None):
    """
    Create a human message at the playground level.
    Stores: playground_id, sender_id (optional), sender_username (optional), content, timestamp
    """
    db = get_db()
    doc = {
        "playground_id": ObjectId(playground_id),
        "sender_id": ObjectId(sender_id) if sender_id else None,
        "sender_username": sender_username,
        "content": content,
        "timestamp": _now(),
    }
    res = await db.messages.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc["playground_id"] = playground_id
    doc["sender_id"] = str(sender_id) if sender_id else None
    return doc


async def list_messages(playground_id: str, limit: int = 100):
    db = get_db()
    cursor = db.messages.find({"playground_id": ObjectId(playground_id)}).sort("timestamp", 1).limit(limit)
    out = []
    async for m in cursor:
        m["_id"] = str(m["_id"])
        m["playground_id"] = str(m["playground_id"]) if m.get("playground_id") else None
        m["sender_id"] = str(m["sender_id"]) if m.get("sender_id") else None
        # keep content and timestamp, normalize keys
        out.append({
            "_id": m["_id"],
            "playground_id": m.get("playground_id"),
            "sender_id": m.get("sender_id"),
            "sender_username": m.get("sender_username"),
            "content": m.get("content"),
            "timestamp": m.get("timestamp"),
        })
    return out
