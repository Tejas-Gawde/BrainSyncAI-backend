from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PlaygroundCreate(BaseModel):
    name: str

class PlaygroundOut(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    created_by: str
    owner: str
    members: List[str]
    created_at: datetime
    updated_at: datetime

class InviteIn(BaseModel):
    username: str
