from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from backend.src.api.database import Base


class User(Base):
    __tablename__ = "web_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    code_expires_at = Column(DateTime, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)