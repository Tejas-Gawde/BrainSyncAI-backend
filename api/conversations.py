from fastapi import APIRouter, Depends, HTTPException, Path
from api.users import get_current_user
from models.message import MessageCreate, MessageOut
from services.message_service import create_message, list_messages
from services.playground_service import get_playground
from services.subject_service import get_subject

router = APIRouter(prefix="/playgrounds/{playground_id}/subjects/{subject_id}/messages", tags=["messages"])

@router.post("/", response_model=MessageOut)
async def post_message(playground_id: str, subject_id: str, payload: MessageCreate, current_user: dict = Depends(get_current_user)):
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    if current_user["_id"] not in pg["members"]:
        raise HTTPException(status_code=403, detail="Not a member")
    subj = await get_subject(subject_id)
    if not subj or subj["playground_id"] != playground_id:
        raise HTTPException(status_code=404, detail="Subject not found in this playground")
    msg = await create_message(subject_id, playground_id, "user", current_user["_id"], payload.message)
    return msg

@router.get("/", response_model=list[MessageOut])
async def get_messages(playground_id: str, subject_id: str, current_user: dict = Depends(get_current_user)):
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    if current_user["_id"] not in pg["members"]:
        raise HTTPException(status_code=403, detail="Not a member")
    # validate subject
    subj = await get_subject(subject_id)
    if not subj or subj["playground_id"] != playground_id:
        raise HTTPException(status_code=404, detail="Subject not found in this playground")
    msgs = await list_messages(subject_id)
    return msgs
