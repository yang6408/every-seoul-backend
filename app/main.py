import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.db.models import newsletter as _newsletter_models  # noqa: F401
from app.db.models import user as _user_models  # noqa: F401
from app.db.session import SessionLocal, init_db
from app.services.ai_service import close_http_client, init_http_client
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.CREATE_DB_TABLES:
        logger.info("Creating database tables")
        init_db()

    init_http_client()
    if settings.ENABLE_SCHEDULER:
        start_scheduler()

    yield

    if settings.ENABLE_SCHEDULER:
        stop_scheduler()
    await close_http_client()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": settings.APP_NAME}


@app.get("/health")
def health_check():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))

    return {"status": "ok", "environment": settings.ENVIRONMENT}
