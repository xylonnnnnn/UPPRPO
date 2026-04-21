from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, false, func, text, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "web_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    img_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default=false())
    verification_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    boards: Mapped[list["Board"]] = relationship(back_populates="owner")
    pins: Mapped[list["Pin"]] = relationship(back_populates="author")


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, server_default=false())
    user_id: Mapped[int] = mapped_column(ForeignKey("web_users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="boards")
    pins: Mapped[list["Pin"]] = relationship(back_populates="board")


class Pin(Base):
    __tablename__ = "pins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    link_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    likes_count: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("web_users.id", ondelete="CASCADE"), nullable=False)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    author: Mapped[User] = relationship(back_populates="pins")
    board: Mapped[Board] = relationship(back_populates="pins")
