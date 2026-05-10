from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.user import User
from app.db.session import ensure_user_profile_columns
from app.schemas.auth import GoogleLoginRequest, GoogleLoginResponse
from app.services.google_auth import verify_google_id_token
from app.services.session_auth import create_session, revoke_session_token
from app.core.config import settings

router = APIRouter()


@router.post("/google", response_model=GoogleLoginResponse)
def login_with_google(
    body: GoogleLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    ensure_user_profile_columns()
    profile = verify_google_id_token(body.credential)
    email = profile["email"]

    user = db.query(User).filter(User.email == email).first()
    if user:
        if not user.is_active:
            user.is_active = True
        user.updated_at = datetime.utcnow()
    else:
        user = User(
            email=email,
            districts=[],
            interests=[],
            has_children=False,
            employment_status="",
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    session_token, session_expires_at = create_session(db, user)
    db.commit()
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
        path="/",
    )

    return GoogleLoginResponse(
        user=user,
        name=profile.get("name") or email,
        picture=profile.get("picture"),
        email=email,
        session_expires_at=session_expires_at.isoformat(),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if session_token:
        revoke_session_token(db, session_token)
        db.commit()
    response.delete_cookie("session_token", path="/")
