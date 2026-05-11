from pydantic import BaseModel


class EventDetail(BaseModel):
    title: str
    date: str
    time: str
    location: str
    location_detail: str
    capacity: int
    registered: int
    description: str
    program: list[dict[str, str]]
    benefits: list[str]
    requirements: list[str]
    contact: str


class PolicyResponse(BaseModel):
    id: int
    title: str
    description: str
    deadline: str
    period: str
    category: str
    status: str
    status_color: str
    views: int
    relevance: int = 0
    support_detail: str
    application_steps: list[str]
    source_url: str | None = None


class PolicyListResponse(BaseModel):
    items: list[PolicyResponse]
    events: list[EventDetail]
