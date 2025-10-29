from fastapi import APIRouter, Depends, HTTPException, status, Path
from api.users import get_current_user
from services.playground_service import (
    create_playground, get_playground, add_member_by_userid, 
    is_member, delete_playground, list_user_playgrounds
)
from services.subject_service import list_subjects
from models.playground import PlaygroundCreate, PlaygroundOut, InviteIn
from db.mongodb import get_db
from bson.objectid import ObjectId

router = APIRouter(prefix="/playgrounds", tags=["playgrounds"])

@router.post("/", response_model=PlaygroundOut)
async def create_pg(payload: PlaygroundCreate, current_user: dict = Depends(get_current_user)):
    pg = await create_playground(payload.name, current_user["_id"])
    return {
        "_id": pg["_id"],
        "name": pg["name"],
        "created_by": pg["created_by"],
        "owner": pg["owner"],
        "members": pg["members"],
        "created_at": pg["created_at"],
        "updated_at": pg["updated_at"],
    }

@router.get("/{playground_id}", response_model=PlaygroundOut)
async def get_pg(playground_id: str = Path(...), current_user: dict = Depends(get_current_user)):
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    if current_user["_id"] not in pg["members"]:
        raise HTTPException(status_code=403, detail="Not a member of this playground")
    return pg

@router.get("/", response_model=list[PlaygroundOut])
async def list_my_playgrounds(current_user: dict = Depends(get_current_user)):
    """Get all playgrounds where the current user is a member"""
    playgrounds = await list_user_playgrounds(current_user["_id"])
    return playgrounds

@router.post("/{playground_id}/invite")
async def invite(playground_id: str, payload: InviteIn, current_user: dict = Depends(get_current_user)):
    # Only owner or members can invite
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    # check inviter is member
    if current_user["_id"] not in pg["members"]:
        raise HTTPException(status_code=403, detail="Not allowed to invite")
    # find user by username
    db = get_db()
    user = await db.users.find_one({"username": payload.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = str(user["_id"])
    await add_member_by_userid(playground_id, user_id)
    return {"message": "user invited (and added) to playground", "user_id": user_id}

@router.delete("/{playground_id}")
async def delete(playground_id: str, current_user: dict = Depends(get_current_user)):
    pg = await get_playground(playground_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Playground not found")
    if current_user["_id"] != pg["owner"]:
        raise HTTPException(status_code=403, detail="Only owner may delete playground")
    await delete_playground(playground_id)
    return {"message": "playground deleted"}
