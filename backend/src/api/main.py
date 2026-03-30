import os
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta, datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session, declarative_base

from backend.src.api.email_config import send_verification_email
from backend.src.api.google_auth import oauth
from backend.src.api.database import get_db, Base, init_db
from backend.src.api.models import User
from backend.src.api.schemas import UserCreate, UserResponse, Token, TokenData, VerifyEmail
from backend.src.api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.src.api.crud import get_user_by_email, get_user_by_username, create_user, verify_user_email, \
    create_google_user, get_user_by_id  # Из первого примера

def generate_code():
    return secrets.randbelow(1000000)

app = FastAPI(title="FastAPI Auth System")

@app.on_event("startup")
async def on_startup():
    await init_db()
    print("✅ База данных инициализирована")

@app.get("/l")
async def test():
    return {"code": generate_code()}

@app.get("/gdb")
async def gdb(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalar_one_or_none()

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_email = await get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    existing_username = await get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Имя пользователя занято")

    code = generate_code()
    expires = datetime.utcnow() + timedelta(minutes=10)

    await create_user(db=db, user=user, code=code, expires=expires)
    await send_verification_email(user.email, code)

    return {"message": "Пользователь создан. Проверьте почту для подтверждения."}
#
#
@app.post("/verify-email")
async def verify_email(data: VerifyEmail, db: AsyncSession = Depends(get_db)):
    success = await verify_user_email(db, data.email, data.code)
    if not success:
        raise HTTPException(status_code=400, detail="Неверный код или код истёк")
    return {"message": "Email подтвержден!"}
#
#
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user == "not_verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтвержден",
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
#
#
@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)
#
#
@app.get("/auth/google")
async def auth_google(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')

    if not user_info:
        raise HTTPException(status_code=400, detail="Ошибка получения данных Google")

    email = user_info.get('email')
    google_id = user_info.get('sub')
    username = user_info.get('name', email.split('@')[0])

    user = await get_user_by_email(db, email)

    if not user:
        user = await create_google_user(db, email, username, google_id)
    else:
        if not user.google_id:
            user.google_id = google_id
            await db.commit()
        if not user.is_verified:
            user.is_verified = True
            await db.commit()

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/users/me", response_model=UserResponse)
# async def read_users_me(current_user: User = Depends(get_current_user)):
#     return current_user
#
# @app.get("/users/{user_id}", response_model=UserResponse)
# async def get_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
#     user = await get_user_by_id(db, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="Пользователь не найден")
#     return user