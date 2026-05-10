from typing import Generator

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.user import User
from app.services.session_auth import get_user_for_token


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    authorization: str = Header(default=""),
    session_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    scheme, _, token = authorization.partition(" ")
    auth_token = token if scheme.lower() == "bearer" and token else session_token
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
        )

    return get_user_for_token(db, auth_token)
