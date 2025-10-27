from bson import ObjectId
from datetime import datetime
from db.mongodb import get_db

def _now():
    return datetime.utcnow()

async def create_playground(name: str, owner_id: str):
    db = get_db()
    now = _now()
    doc = {
        "name": name,
        "created_by": ObjectId(owner_id),
        "owner": ObjectId(owner_id),
        "members": [ObjectId(owner_id)],
        "created_at": now,
        "updated_at": now,
    }
    res = await db.playgrounds.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc["created_by"] = owner_id
    doc["owner"] = owner_id
    doc["members"] = [owner_id]
    return doc

async def get_playground(playground_id: str):
    db = get_db()
    pg = await db.playgrounds.find_one({"_id": ObjectId(playground_id)})
    if not pg:
        return None
    # normalize
    pg["_id"] = str(pg["_id"])
    pg["created_by"] = str(pg["created_by"])
    pg["owner"] = str(pg["owner"])
    pg["members"] = [str(m) for m in pg.get("members", [])]
    return pg

async def is_member(playground_id: str, user_id: str) -> bool:
    db = get_db()
    pg = await db.playgrounds.find_one({"_id": ObjectId(playground_id), "members": ObjectId(user_id)})
    return pg is not None

async def add_member_by_userid(playground_id: str, user_id: str):
    db = get_db()
    await db.playgrounds.update_one(
        {"_id": ObjectId(playground_id)},
        {"$addToSet": {"members": ObjectId(user_id)}, "$set": {"updated_at": _now()}}
    )
    return await get_playground(playground_id)

async def remove_member_by_userid(playground_id: str, user_id: str):
    db = get_db()
    await db.playgrounds.update_one(
        {"_id": ObjectId(playground_id)},
        {"$pull": {"members": ObjectId(user_id)}, "$set": {"updated_at": _now()}}
    )
    return await get_playground(playground_id)

async def delete_playground(playground_id: str):
    db = get_db()
    await db.playgrounds.delete_one({"_id": ObjectId(playground_id)})
    # Optionally remove related subjects/messages
    await db.subjects.delete_many({"playground_id": ObjectId(playground_id)})
    await db.messages.delete_many({"playground_id": ObjectId(playground_id)})
    return True
