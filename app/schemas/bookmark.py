from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BookmarkItemType = Literal["newsletter", "policy"]


class BookmarkCreate(BaseModel):
    item_type: BookmarkItemType
    item_id: int = Field(ge=1)


class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    item_type: BookmarkItemType
    item_id: int
    created_at: datetime


class BookmarkListResponse(BaseModel):
    items: list[BookmarkResponse]
