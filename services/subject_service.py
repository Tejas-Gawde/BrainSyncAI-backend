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


async def append_summary_to_subject(subject_id: str, youtube_link: str, summary: str, added_by: str | None = None):
    """
    Append a generated summary to a subject document.
    Adds an entry to the `summaries` array on the subject like:
      { youtube_link, summary, added_by, timestamp }
    """
    db = get_db()
    entry = {
        "youtube_link": youtube_link,
        "summary": summary,
        "added_by": ObjectId(added_by) if added_by else None,
        "added_at": _now(),
    }
    await db.subjects.update_one({"_id": ObjectId(subject_id)}, {"$push": {"summaries": entry}, "$set": {"updated_at": _now()}})
    return await get_subject(subject_id)


async def append_conversation_to_subject(subject_id: str, question: str, answer: str, pdf_filename: str | None = None, added_by: str | None = None):
        """
        Append a conversation entry (question + answer) to a subject.
        Stores into `conversations` array on the subject document:
            { question, answer, pdf_filename, added_by, added_at }
        """
        db = get_db()
        entry = {
                "question": question,
                "answer": answer,
                "pdf_filename": pdf_filename,
                "added_by": ObjectId(added_by) if added_by else None,
                "added_at": _now(),
        }
        await db.subjects.update_one({"_id": ObjectId(subject_id)}, {"$push": {"conversations": entry}, "$set": {"updated_at": _now()}})
        return await get_subject(subject_id)
