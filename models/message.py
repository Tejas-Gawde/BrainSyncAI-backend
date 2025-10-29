from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: str = Field(..., alias="_id")
    playground_id: str
    sender_id: Optional[str]
    sender_username: Optional[str]
    content: str
    timestamp: datetime
