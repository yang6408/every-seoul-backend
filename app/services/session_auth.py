import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.session import UserSession
from app.db.models.user import User

SESSION_TTL_DAYS = 30


def create_session(db: Session, user: User) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=expires_at,
        )
    )
    return token, expires_at


def revoke_session_token(db: Session, token: str) -> None:
    session = (
        db.query(UserSession)
        .filter(UserSession.token_hash == hash_session_token(token))
        .first()
    )
    if session:
        db.delete(session)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_user_for_token(db: Session, token: str) -> User:
    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == hash_session_token(token),
            UserSession.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
        )

    user = db.query(User).filter(User.id == session.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 사용자입니다.",
        )

    return user
