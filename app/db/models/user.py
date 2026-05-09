from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    districts = Column(ARRAY(String), default=list)
    has_children = Column(Boolean, default=False)
    children_count = Column(Integer, nullable=True)
    employment_status = Column(String(50), default="")
    interests = Column(ARRAY(String), default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    matches = relationship(
        "UserNewsletterMatch",
        back_populates="user",
        cascade="all, delete-orphan",
    )
