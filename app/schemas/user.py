from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    districts: List[str] = Field(default_factory=list, description="관심 자치구 목록")
    interests: List[str] = Field(default_factory=list, description="관심 키워드/태그 목록")


class UserUpdate(BaseModel):
    districts: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    email: str
    districts: List[str]
    interests: List[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
