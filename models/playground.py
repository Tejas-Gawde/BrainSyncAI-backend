from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from models.message import MessageOut

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
    # playground-level messages (most recent first by default from service)
    messages: Optional[List[MessageOut]] = []

class InviteIn(BaseModel):
    username: str
