from fastapi import APIRouter

from app.api.endpoints import admin, newsletter, user

api_router = APIRouter()

api_router.include_router(newsletter.router, prefix="/newsletters", tags=["Newsletter"])
api_router.include_router(user.router, prefix="/users", tags=["User"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
