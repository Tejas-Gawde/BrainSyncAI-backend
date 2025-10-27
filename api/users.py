from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from core.config import settings
from db.mongodb import get_db
from core.security import bytes_to_base64
from services import auth_service
from bson.binary import Binary
from bson.objectid import ObjectId
from typing import Optional
from jose import jwt

router = APIRouter(prefix="/users", tags=["users"])

def USERS():
    return get_db().users


def get_token_from_cookie(request: Request):
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token

async def get_current_user(request: Request):
    token = get_token_from_cookie(request)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = await USERS().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # convert id
    user["_id"] = str(user["_id"])
    # attach avatar as base64
    avatar = user.get("avatar")
    if avatar:
        # avatar is BSON Binary
        user["avatar"] = bytes_to_base64(avatar)
    else:
        user["avatar"] = None
    return user

@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    # returns the user object prepared in dependency
    return current_user

@router.put("/me")
async def update_me(
    request: Request,
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user)
):
    update = {}
    if username and username != current_user["username"]:
        # ensure uniqueness
        existing = await USERS().find_one({"username": username})
        if existing and str(existing["_id"]) != current_user["_id"]:
            raise HTTPException(status_code=400, detail="Username already taken")
        update["username"] = username
    if email and email != current_user["email"]:
        existing = await USERS().find_one({"email": email})
        if existing and str(existing["_id"]) != current_user["_id"]:
            raise HTTPException(status_code=400, detail="Email already taken")
        update["email"] = email
    if avatar:
        avatar_bytes = await avatar.read()
        update["avatar"] = Binary(avatar_bytes)
    if not update:
        raise HTTPException(status_code=400, detail="Nothing to update")
    await USERS().update_one({"_id": ObjectId(current_user["_id"])}, {"$set": update})
    user = await USERS().find_one({"_id": ObjectId(current_user["_id"])})
    user["_id"] = str(user["_id"])
    user["avatar"] = bytes_to_base64(user.get("avatar")) if user.get("avatar") else None
    return user

@router.post("/change-password")
async def change_password(body: dict, current_user=Depends(get_current_user)):
    old_password = body.get("old_password")
    new_password = body.get("new_password")
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Old password and newpassword required")
    ok = await auth_service.change_password(current_user["_id"], old_password, new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Old password incorrect")
    return {"message": "Password changed successfully"}
