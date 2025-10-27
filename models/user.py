from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    username: str
    email: EmailStr
    avatar: Optional[str] = None 

class LoginIn(BaseModel):
    username: str
    password: str

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str
