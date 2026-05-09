from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1, description="Google Identity Services ID token")


class GoogleLoginResponse(BaseModel):
    user: UserResponse
    provider: str = "google"
    name: str
    picture: str | None = None
    email: EmailStr
