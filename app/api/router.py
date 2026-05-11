from fastapi import APIRouter

from app.api.endpoints import admin, auth, life_info, newsletter, notification, policy, user

api_router = APIRouter()

api_router.include_router(newsletter.router, prefix="/newsletters", tags=["Newsletter"])
api_router.include_router(user.router, prefix="/users", tags=["User"])
api_router.include_router(life_info.router, prefix="/life-info", tags=["LifeInfo"])
api_router.include_router(policy.router, prefix="/policies", tags=["Policy"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(notification.router, prefix="/notifications", tags=["Notification"])
