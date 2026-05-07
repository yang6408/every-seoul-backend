from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.models import newsletter as _newsletter_models  # noqa: F401 — Base 등록
from app.db.models import user as _user_models  # noqa: F401 — Base 등록
from app.services.ai_service import close_http_client, init_http_client
from app.tasks.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_http_client()
    if settings.ENABLE_SCHEDULER:
        start_scheduler()
    yield
    if settings.ENABLE_SCHEDULER:
        stop_scheduler()
    await close_http_client()


app = FastAPI(title="에브리 서울 API", version="1.0", lifespan=lifespan)

app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "에브리 서울 API"}
