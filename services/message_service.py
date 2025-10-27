from bson import ObjectId
from datetime import datetime
from db.mongodb import get_db

def _now():
    return datetime.utcnow()

async def create_message(topic_id: str, playground_id: str, sender_type: str, sender_id: str | None, message: str):
    db = get_db()
    doc = {
        "topic_id": ObjectId(topic_id),
        "playground_id": ObjectId(playground_id),
        "sender_type": sender_type,  # "user" | "ai"
        "sender_id": ObjectId(sender_id) if sender_id else None,
        "message": message,
        "timestamp": _now(),
    }
    res = await db.messages.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc["topic_id"] = topic_id
    doc["playground_id"] = playground_id
    doc["sender_id"] = str(sender_id) if sender_id else None
    return doc

async def list_messages(topic_id: str, limit: int = 100):
    db = get_db()
    cursor = db.messages.find({"topic_id": ObjectId(topic_id)}).sort("timestamp", 1).limit(limit)
    out = []
    async for m in cursor:
        m["_id"] = str(m["_id"])
        m["topic_id"] = str(m["topic_id"])
        m["playground_id"] = str(m["playground_id"])
        m["sender_id"] = str(m["sender_id"]) if m.get("sender_id") else None
        out.append(m)
    return out
