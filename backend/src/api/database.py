import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()