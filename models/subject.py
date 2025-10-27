from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SubjectCreate(BaseModel):
    title: str
    description: Optional[str] = None

class SubjectOut(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    description: Optional[str]
    created_by: str
    playground_id: str
    created_at: datetime
    updated_at: datetime
