from fastapi import APIRouter

from app.api.endpoints import admin, auth, newsletter, user

api_router = APIRouter()

api_router.include_router(newsletter.router, prefix="/newsletters", tags=["Newsletter"])
api_router.include_router(user.router, prefix="/users", tags=["User"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
