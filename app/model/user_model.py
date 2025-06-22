from pydantic import BaseModel, EmailStr, Field

from typing import Optional
from datetime import datetime

class User(BaseModel):
    email: EmailStr
    password: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)