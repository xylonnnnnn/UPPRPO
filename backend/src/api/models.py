from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "web_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(Integer, nullable=True)
    code_expires_at = Column(DateTime, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    boards = relationship("Board", back_populates="owner", cascade="all, delete-orphan")
    pins = relationship("Pin", back_populates="author", cascade="all, delete-orphan")

class Pin(Base):
    __tablename__ = "pins"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    link_url = Column(String(500), nullable=True)

    # image_width = Column(Integer, default=0)
    # image_height = Column(Integer, default=0)
    # aspect_ratio = Column(Float, default=1.0)

    likes_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)

    user_id = Column(Integer, ForeignKey("web_users.id", ondelete="CASCADE"), nullable=False)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)

    author = relationship("User", back_populates="pins")
    board = relationship("Board", back_populates="pins")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_deleted = Column(Boolean, default=False)

class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("web_users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="boards")
    pins = relationship("Pin", back_populates="board", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)
