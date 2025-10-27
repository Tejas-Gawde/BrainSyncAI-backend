from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class MessageCreate(BaseModel):
    message: str

class MessageOut(BaseModel):
    id: str = Field(..., alias="_id")
    topic_id: str
    sender_type: Literal["user", "ai"]
    sender_id: Optional[str]
    message: str
    timestamp: datetime
