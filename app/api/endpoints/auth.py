from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.user import User
from app.db.session import ensure_user_profile_columns
from app.schemas.auth import GoogleLoginRequest, GoogleLoginResponse
from app.services.google_auth import verify_google_id_token

router = APIRouter()


@router.post("/google", response_model=GoogleLoginResponse)
def login_with_google(body: GoogleLoginRequest, db: Session = Depends(get_db)):
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

    return GoogleLoginResponse(
        user=user,
        name=profile.get("name") or email,
        picture=profile.get("picture"),
        email=email,
    )
