from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class NewsletterSummary(BaseModel):
    id: int
    title: str
    publish_date: datetime
    tags: List[str]
    district: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NewsletterDetail(BaseModel):
    id: int
    title: str
    publish_date: datetime
    ai_briefing: Dict[str, Any]
    tags: List[str]
    district: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def _extract_district(self) -> "NewsletterDetail":
        if self.district is None and self.ai_briefing:
            self.district = self.ai_briefing.get("district")
        return self


class NewsletterListResponse(BaseModel):
    total: int
    items: List[NewsletterSummary]


class FeedItem(BaseModel):
    newsletter: NewsletterDetail
    match_score: int
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


class UserFeedResponse(BaseModel):
    total: int
    items: List[FeedItem]


class FeedRefreshResponse(BaseModel):
    matched: int
    message: str


class PipelineTriggerResponse(BaseModel):
    status: str
    message: str
