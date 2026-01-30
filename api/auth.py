from fastapi import APIRouter, UploadFile, File, Form,  HTTPException, Response
from services import auth_service
from core.config import settings
from core.security import bytes_to_base64
from models.user import UserOut, LoginIn
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    avatar: Optional[UploadFile] = File(None),   # user-uploaded file (optional)
    avatar_url: Optional[str] = Form(None)       # predefined avatar URL (optional)
):

    
    # check if user already exists
    existing = await auth_service.find_user_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    existing_e = await auth_service.find_user_by_email(email)
    if existing_e:
        raise HTTPException(status_code=400, detail="Email already exists")

    # handle avatar input
    avatar_bytes = None
    avatar_url_to_store = None
    if avatar:
        # user uploaded a file - store as bytes
        avatar_bytes = await avatar.read()
    elif avatar_url:
        # user selected a predefined avatar - store the URL
        avatar_url_to_store = avatar_url
    else:
        raise HTTPException(status_code=400, detail="Avatar required (upload or select one)")

    # create user
    user = await auth_service.create_user(username, email, password, avatar_bytes, avatar_url_to_store)

    # prepare response avatar
    if avatar_bytes:
        avatar_response = bytes_to_base64(avatar_bytes)
    else:
        avatar_response = avatar_url_to_store
    
    
    # Create JWT token and set cookie so user is automatically logged in after signup
    token = auth_service.create_jwt_for_user(user)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=60*settings.JWT_EXP_MINUTES
    )
        
    user_out = {
        "_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "avatar": avatar_response
    }

    return user_out


@router.post("/login")
async def login(response: Response, form_data: LoginIn):
    user = await auth_service.verify_user_credentials(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth_service.create_jwt_for_user(user)
    # set cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=60*settings.JWT_EXP_MINUTES
    )
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(settings.COOKIE_NAME)
    return {"message": "Logged out"}

@router.post("/forgot-password")
async def forgot_password(payload: dict):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email required")
    token = await auth_service.generate_password_reset(email)
    if not token:
        # do not reveal whether email exists (security), but we simulate returning token
        return {"message": "If email exists, reset token was sent (simulated).", "simulated_token": None}
    # in real app: send email with token
    return {"message": "Password reset token generated (simulated).", "simulated_token": token}

@router.post("/reset-password")
async def reset_password(payload: dict):
    token = payload.get("token")
    new_password = payload.get("new_password")
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and new_password required")
    ok = await auth_service.verify_and_reset_password(token, new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"message": "Password reset successful"}
