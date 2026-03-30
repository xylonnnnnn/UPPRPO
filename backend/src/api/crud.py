from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.src.api.models import User
from backend.src.api.schemas import UserCreate


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result if result else None

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result if result else None

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result if result else None

async def create_user(db: AsyncSession, user: UserCreate, code, expires):
    from backend.src.api.auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        verification_code=code,
        code_expires_at=expires,
        is_verified=False
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def verify_user_email(db: AsyncSession, email: str, code: str) -> bool:
    user = await get_user_by_email(db, email)
    if not user or user.verification_code != code:
        return False
    if user.code_expires_at and user.code_expires_at < datetime.utcnow():
        return False

    user.is_verified = True
    user.verification_code = None
    user.code_expires_at = None
    await db.commit()
    return True

async def create_google_user(db: AsyncSession, email: str, username: str, google_id: str) -> User:
    user = User(
        email=email,
        username=username,
        google_id=google_id,
        is_verified=True,
        hashed_password=None
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user