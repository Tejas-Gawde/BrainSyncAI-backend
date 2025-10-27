from bson import ObjectId
from datetime import datetime
from db.mongodb import get_db

def _now():
    return datetime.utcnow()

async def create_subject(title: str, description: str, created_by: str, playground_id: str):
    db = get_db()
    doc = {
        "title": title,
        "description": description,
        "created_by": ObjectId(created_by),
        "playground_id": ObjectId(playground_id),
        "created_at": _now(),
        "updated_at": _now(),
    }
    res = await db.subjects.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc["created_by"] = created_by
    doc["playground_id"] = playground_id
    return doc

async def get_subject(subject_id: str):
    db = get_db()
    s = await db.subjects.find_one({"_id": ObjectId(subject_id)})
    if not s:
        return None
    s["_id"] = str(s["_id"])
    s["created_by"] = str(s["created_by"])
    s["playground_id"] = str(s["playground_id"])
    return s

async def list_subjects(playground_id: str):
    db = get_db()
    cursor = db.subjects.find({"playground_id": ObjectId(playground_id)}).sort("created_at", 1)
    out = []
    async for s in cursor:
        s["_id"] = str(s["_id"])
        s["created_by"] = str(s["created_by"])
        s["playground_id"] = str(s["playground_id"])
        out.append(s)
    return out
