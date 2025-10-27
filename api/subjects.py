from fastapi import APIRouter, Depends, HTTPException, Path
from api.users import get_current_user
from models.subject import SubjectCreate, SubjectOut
from services.subject_service import create_subject, list_subjects, get_subject
from services.playground_service import get_playground, is_member

router = APIRouter(prefix="/playgrounds/{playground_id}/subjects", tags=["subjects"])

@router.post("/", response_model=SubjectOut)
async def create_subj(playground_id: str, payload: SubjectCreate, current_user: dict = Depends(get_current_user)):
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    if current_user["_id"] not in pg["members"]:
        raise HTTPException(status_code=403, detail="Not a member")
    subj = await create_subject(payload.title, payload.description or "", current_user["_id"], playground_id)
    return {
        "_id": subj["_id"],
        "title": subj["title"],
        "description": subj["description"],
        "created_by": subj["created_by"],
        "playground_id": subj["playground_id"],
        "created_at": subj["created_at"],
        "updated_at": subj["updated_at"],
    }

@router.get("/", response_model=list[SubjectOut])
async def list_subj(playground_id: str, current_user: dict = Depends(get_current_user)):
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    if current_user["_id"] not in pg["members"]:
        raise HTTPException(status_code=403, detail="Not a member")
    subs = await list_subjects(playground_id)
    return subs

@router.get("/{subject_id}", response_model=SubjectOut)
async def get_one(playground_id: str, subject_id: str, current_user: dict = Depends(get_current_user)):
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    if current_user["_id"] not in pg["members"]:
        raise HTTPException(status_code=403, detail="Not a member")
    s = await get_subject(subject_id)
    if not s:
        raise HTTPException(status_code=404, detail="Subject not found")
    return s
