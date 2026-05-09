from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    age: Optional[int] = Field(default=None, ge=0, le=130)
    districts: List[str] = Field(default_factory=list, description="관심 자치구 목록")
    has_children: bool = False
    children_count: Optional[int] = Field(default=None, ge=0)
    employment_status: str = ""
    interests: List[str] = Field(default_factory=list, description="관심 키워드/태그 목록")


class UserUpdate(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=130)
    districts: Optional[List[str]] = None
    has_children: Optional[bool] = None
    children_count: Optional[int] = Field(default=None, ge=0)
    employment_status: Optional[str] = None
    interests: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    email: str
    age: Optional[int] = None
    districts: List[str]
    has_children: bool
    children_count: Optional[int] = None
    employment_status: str
    interests: List[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
