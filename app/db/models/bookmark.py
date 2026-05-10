from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String

from app.db.session import Base


class UserBookmark(Base):
    __tablename__ = "user_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_user_bookmark_item", "user_id", "item_type", "item_id", unique=True),
    )
