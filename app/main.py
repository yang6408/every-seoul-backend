from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.tasks.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="에브리 서울 API", version="1.0", lifespan=lifespan)

app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "에브리 서울 API"}
