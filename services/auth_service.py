from bson import ObjectId
from bson.binary import Binary
from datetime import datetime, timedelta, timezone
import secrets
from core.security import hash_password, verify_password, create_access_token
from core.config import settings
from db.mongodb import get_db

def USERS():
    return get_db().users

async def create_user(username: str, email: str, password: str, avatar_bytes: bytes = None, avatar_url: str = None):
    hashed = hash_password(password)
    
    # Store avatar as bytes (for uploads) or URL string (for predefined avatars)
    avatar_value = None
    if avatar_bytes:
        avatar_value = Binary(avatar_bytes)
    elif avatar_url:
        avatar_value = avatar_url
    
    user = {
        "username": username,
        "email": email,
        "password": hashed,
        "avatar": avatar_value,
        "created_at": datetime.now(timezone.utc),
        "password_reset": None 
    }
    res = await USERS().insert_one(user)
    user["_id"] = str(res.inserted_id)
    return user

async def find_user_by_username(username: str):
    u = await USERS().find_one({"username": username})
    return u

async def find_user_by_email(email: str):
    u = await USERS().find_one({"email": email})
    return u

async def find_user_by_id(user_id: str):
    u = await USERS().find_one({"_id": ObjectId(user_id)})
    return u

async def verify_user_credentials(username: str, password: str):
    u = await find_user_by_username(username)
    if not u: 
        return None
    if verify_password(password, u["password"]):
        u["_id"] = str(u["_id"])
        return u
    return None

async def update_user(user_id: str, update_dict: dict):
    await USERS().update_one({"_id": ObjectId(user_id)}, {"$set": update_dict})
    return await find_user_by_id(user_id)

async def change_password(user_id: str, old_password: str, new_password: str):
    u = await find_user_by_id(user_id)
    if not u:
        return False
    if not verify_password(old_password, u["password"]):
        return False
    hashed = hash_password(new_password)
    await USERS().update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed}})
    return True

async def generate_password_reset(email: str):
    u = await find_user_by_email(email)
    if not u:
        return None
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXP_MINUTES)
    await USERS().update_one({"_id": u["_id"]}, {"$set": {"password_reset": {"token": token, "expires_at": expires}}})
    return token

async def verify_and_reset_password(token: str, new_password: str):
    u = await USERS().find_one({"password_reset.token": token})
    if not u:
        return False
    info = u.get("password_reset")
    if not info:
        return False
    if info["expires_at"] < datetime.utcnow():
        return False
    hashed = hash_password(new_password)
    await USERS().update_one({"_id": u["_id"]}, {"$set": {"password": hashed, "password_reset": None}})
    return True

def create_jwt_for_user(user: dict):
    payload = {"user_id": str(user["_id"]), "username": user["username"]}
    token = create_access_token(payload)
    return token
