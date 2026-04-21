from __future__ import annotations

from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Board, Pin, User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    res = await session.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()


async def verify_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(session, email)
    if not user or not user.hashed_password:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


async def get_user_boards(session: AsyncSession, user_id: int) -> list[Board]:
    res = await session.execute(
        select(Board)
        .where(Board.user_id == user_id)
        .order_by(Board.created_at.desc(), Board.id.desc())
    )
    return list(res.scalars().all())


async def get_board_for_user(session: AsyncSession, board_id: int, user_id: int) -> Optional[Board]:
    res = await session.execute(
        select(Board).where((Board.id == board_id) & (Board.user_id == user_id))
    )
    return res.scalar_one_or_none()


async def get_board_by_name_for_user(session: AsyncSession, name: str, user_id: int) -> Optional[Board]:
    res = await session.execute(
        select(Board).where((Board.name == name) & (Board.user_id == user_id))
    )
    return res.scalar_one_or_none()


async def create_board(
    session: AsyncSession,
    user_id: int,
    name: str,
    description: Optional[str] = None,
    is_private: bool = False,
) -> Board:
    existing_board = await get_board_by_name_for_user(session, name=name, user_id=user_id)
    if existing_board:
        raise ValueError("Board with this name already exists")

    board = Board(
        user_id=user_id,
        name=name,
        description=description,
        is_private=is_private,
    )
    session.add(board)
    await session.commit()
    await session.refresh(board)
    return board


async def create_pin(
    session: AsyncSession,
    *,
    user_id: int,
    board_id: int,
    title: str,
    description: Optional[str],
    image_url: Optional[str],
    link_url: Optional[str] = None,
) -> Pin:
    board = await get_board_for_user(session, board_id=board_id, user_id=user_id)
    if not board:
        raise ValueError("Board not found or does not belong to user")

    pin = Pin(
        user_id=user_id,
        board_id=board_id,
        title=title,
        description=description,
        image_url=image_url,
        link_url=link_url,
        likes_count=0,
    )
    session.add(pin)
    await session.commit()
    await session.refresh(pin)
    return pin
