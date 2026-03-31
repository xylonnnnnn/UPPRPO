import os
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta, datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile
from fastapi.params import File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session, declarative_base
from starlette.middleware.sessions import SessionMiddleware

from email_config import send_verification_email
from google_auth import oauth
from database import get_db, Base, init_db
from models import User, Pin, Board
from schemas import UserCreate, Token, TokenData, VerifyEmail, PinCreate, PinResponse, \
    UserDelete
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, generate_code
)
from crud import get_user_by_email, get_user_by_username, create_user, verify_user_email, \
    create_google_user, get_user_by_id  # Из первого примера

load_dotenv()

CLOUDFLARE_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CLOUDFLARE_IMAGES_API_KEY = os.getenv("CF_IMAGES_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


app = FastAPI(title="FastAPI Auth System")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)),
    https_only=False,
    max_age=3600
)

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
    return result.scalars().all()

@app.delete("/del_user")
async def delete_user(user: UserDelete, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(delete(User).where(User.username == user.username))
        await db.commit()

        if result.rowcount:
            return {"message": "success"}
        raise HTTPException(status_code=400, detail="Такого пользователя нет")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_email = await get_user_by_email(db, user.email)
    print(user.email, existing_email)
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

@app.post("/verify-email")
async def verify_email(data: VerifyEmail, db: AsyncSession = Depends(get_db)):
    success = await verify_user_email(db, data.email, str(data.code))
    if not success:
        raise HTTPException(status_code=400, detail="Неверный код или код истёк")
    return {"message": "Email подтвержден!"}


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


@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


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

@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    print(f"🔍 Account ID: {CLOUDFLARE_ACCOUNT_ID}")
    print(f"🔍 API Key starts with: {CLOUDFLARE_IMAGES_API_KEY[:10] if CLOUDFLARE_IMAGES_API_KEY else 'None'}...")

    # 🔍 Проверка на пустоту
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_IMAGES_API_KEY:
        raise HTTPException(status_code=500, detail="Cloudflare credentials not configured")

    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"

    print(f"🔍 Request URL: {url}")

    headers = {"Authorization": f"Bearer {CLOUDFLARE_IMAGES_API_KEY}"}
    file_content = await file.read()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            files={"file": (file.filename, file_content, file.content_type)}
        )
        print(f"🔍 Response Status: {response.status_code}")
        print(f"🔍 Response Body: {response.text}")  # ← Покажет полную ошибку от Cloudflare
        result = response.json()

    if result.get("success"):
        image_id = result["result"]["id"]
        return {
            "image_url": f"https://imagedelivery.net/{CLOUDFLARE_ACCOUNT_ID}/{image_id}/public",
            "image_id": image_id
        }

    print(f"❌ Cloudflare error: {result}")
    raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {result.get('errors', ['Unknown'])}")

@app.post("/pins/", response_model=PinResponse)
async def create_pin(
        pin: PinCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    board_result = await db.execute(
        select(Board).where((Board.id == pin.board_id) & (Board.user_id == current_user.id))
    )
    board = board_result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена или недоступна")

    aspect_ratio = pin.image_width / pin.image_height if pin.image_width and pin.image_height else 1.0

    db_pin = Pin(
        **pin.model_dump(),
        user_id=current_user.id,
        aspect_ratio=aspect_ratio,
        likes_count=0,
        saves_count=0
    )

    db.add(db_pin)
    await db.commit()
    await db.refresh(db_pin)

    return db_pin

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