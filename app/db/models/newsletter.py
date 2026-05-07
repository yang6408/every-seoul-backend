from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class Newsletter(Base):
    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, index=True)
    publish_date = Column(DateTime, default=datetime.now(), index=True)  # 새벽 발행일
    title = Column(String(255), nullable=False)

    ai_briefing = Column(JSONB, nullable=False, default={})

    tags = Column(ARRAY(String), default=[])

    matches = relationship("UserNewsletterMatch", back_populates="newsletter")


class UserNewsletterMatch(Base):
    __tablename__ = "user_newsletter_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    newsletter_id = Column(
        Integer, ForeignKey("newsletters.id", ondelete="CASCADE"), nullable=False
    )

    match_score = Column(Integer, default=0)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    newsletter = relationship("Newsletter", back_populates="matches")
    user = relationship("User", back_populates="matches")

    __table_args__ = (
        Index("idx_user_newsletter", "user_id", "newsletter_id", unique=True),
    )
