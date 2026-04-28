import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta, datetime
from typing import List

from dotenv import load_dotenv
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, Query, Body
from fastapi.params import File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from schemas import PinResponse, UserPublic, UserProfile
from sqlalchemy.orm import Session, declarative_base, selectinload, joinedload
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from cache import pins_key_builder, invalidate_pins_cache
from email_config import send_verification_email
from google_auth import oauth
from database import get_db, Base, reset_database
from models import User, Pin, Board, PinLike, PinComments
from schemas import UserCreate, Token, TokenData, VerifyEmail, PinCreate, PinResponse, \
    UserDelete, BoardCreate, BoardResponse, PaginatedResponse, PaginationMeta
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, generate_code
)
from crud import get_user_by_email, get_user_by_username, create_user, verify_user_email, \
    create_google_user, get_user_by_id  # Из первого примера
from storage import UPLOADS_DIR, ensure_upload_dirs, save_upload_file, image_path_to_url, delete_stored_image

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

logger = logging.getLogger(__name__)

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Запрещаем браузеру кешировать ответы API
        if request.url.path.startswith("/pins") or request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_upload_dirs()
    redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    FastAPICache.init(
        RedisBackend(redis),
        prefix="onlyfansRuslana:",
        key_builder=pins_key_builder,
        expire=60,
        enable=True
    )
    logger.info("FastAPICache initialized with Redis")
    yield
    await redis.close()

app = FastAPI(title="FastAPI Auth System", lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)),
    https_only=False,
    max_age=3600
)

# 🔹 2. CORSMiddleware (для фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(NoCacheMiddleware)

@app.delete("/reset")
async def reset():
    await reset_database()
    return {"mes":"oke"}

@app.get("/l", tags=["health check"])
async def test():
    return {"code": generate_code()}

@app.get("/gdb", tags=["health check"])
async def gdb(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

@app.delete("/delete/user", tags=["delete"])
async def delete_user(user: UserDelete, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(delete(User).where(User.username == user.username))
        await db.commit()

        if result.rowcount:
            await invalidate_pins_cache()
            return {"message": "success"}
        raise HTTPException(status_code=400, detail="Такого пользователя нет")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/board/{board_id}", tags=["delete"])
async def delete_board(
        board_id:int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        board = (
            await db.execute(
                select(Board)
                .where(Board.id == board_id)
                .options(selectinload(Board.pins))
            )
        ).scalar_one_or_none()

        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Доска не найден"
            )

        if board.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для удаления этой доски"
            )
        for pin in board.pins:
            delete_stored_image(pin.image_url)
        await db.delete(board)
        await db.commit()
        await invalidate_pins_cache()
        return {"message": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/pin/{pin_id}", tags=["delete"])
async def delete_pin(
        pin_id:int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:

        pin = (await db.execute(select(Pin).where(Pin.id == pin_id))).scalar_one_or_none()

        if not pin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пин не найден"
            )

        if pin.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для удаления этого пина"
            )
        delete_stored_image(pin.image_url)
        await db.delete(pin)
        await db.commit()
        await invalidate_pins_cache()
        return {"message": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/comment/{comment_id}", tags=["delete"])
async def delete_comment(
        comment_id:int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:

        result = await db.execute(
            select(PinComments).where(PinComments.id == comment_id)
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Комментарий не найден"
            )

        if comment.user_id != current_user.id:
            pin_result = await db.execute(
                select(Pin).where(Pin.id == comment.pin_id)
            )
            pin = pin_result.scalar_one_or_none()

            if not pin or pin.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав для удаления этого комментария"
                )

        await db.delete(comment)
        await db.commit()

        await invalidate_pins_cache()
        return {"message": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["mail"])
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

@app.post("/verify-email", tags=["verify"])
async def verify_email(data: VerifyEmail, db: AsyncSession = Depends(get_db)):
    success = await verify_user_email(db, data.email, data.code)
    if not success:
        raise HTTPException(status_code=400, detail="Неверный код или код истёк")
    return {"message": "Email подтвержден!"}


@app.post("/token", response_model=Token, tags=["mail"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # if user == "not_verified":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Email не подтвержден",
    #     )
    # print(user)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/login/google", tags=["google"])
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google", tags=["google"])
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
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
    redirect_url = f"{frontend_url}/auth/google/callback#access_token={access_token}&token_type=bearer"

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)

@app.post("/create/board", response_model=BoardResponse, tags=["Create"])
async def create_board(board: BoardCreate,
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):

    if (await db.execute(
            select(Board).where((Board.name == board.name) & (Board.user_id == current_user.id)))
        ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="доска с таким именем уже есть")

    db_board = Board(
        **board.model_dump(),
        user_id=current_user.id
    )

    db.add(db_board)
    await db.commit()
    await db.refresh(db_board)

    return db_board

@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    image_path = await save_upload_file(file)
    return {"image_url": image_path_to_url(image_path)}

@app.post("/create/pins/", response_model=PinResponse, tags=["Create"])
async def create_pin(
        pin: PinCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    board_result = await db.execute(
        select(Board)
        .where((Board.id == pin.board_id) & (Board.user_id == current_user.id))
    )
    board = board_result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена или недоступна")

    # aspect_ratio = pin.image_width / pin.image_height if pin.image_width and pin.image_height else 1.0

    db_pin = Pin(
        **{**pin.model_dump(), "image_url": image_path_to_url(pin.image_url)},
        user_id=current_user.id,
        # aspect_ratio=aspect_ratio,
        likes_count=0
    )

    db.add(db_pin)
    await db.commit()
    await db.refresh(db_pin)

    result = (await db.execute(select(Pin).where(db_pin.id == Pin.id).options(joinedload(Pin.author),selectinload(Pin.comments)))).scalar_one_or_none()

    await invalidate_pins_cache()
    return result

@app.get("/pins/{pin_id}", response_model=PinResponse, tags=["Pin"])
async def get_pin(pin_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    pin = (await db.execute(select(Pin).where(Pin.id == pin_id).options(joinedload(Pin.author),selectinload(Pin.comments)))).scalar_one_or_none()

    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")

    pin_is_liked = (await db.execute(select(PinLike).where((PinLike.pin_id == pin_id) & (PinLike.user_id == current_user.id)))).scalar_one_or_none()

    if pin_is_liked:
        pin.is_liked = True

    return pin


@app.post("/pins/{pin_id}/like", response_model=PinResponse)
async def toggle_like(
        pin_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Pin)
        .where(Pin.id == pin_id)
        .options(
            joinedload(Pin.author),  # 🔥 Загружаем автора
            selectinload(Pin.comments)  # 🔥 Загружаем комментарии
        )
    )
    pin = result.scalar_one_or_none()
    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")

    like = (await db.execute(
        select(PinLike).where((PinLike.pin_id == pin_id) & (current_user.id == PinLike.user_id))
    )).scalar_one_or_none()

    if like:
        await db.delete(like)
        pin.likes_count = max(0, pin.likes_count - 1)
        action=False
    else:
        db.add(PinLike(pin_id=pin_id, user_id=current_user.id))
        pin.likes_count += 1
        action=True

    await db.commit()
    await db.refresh(pin, attribute_names=["comments"])
    pin.is_liked = action
    await invalidate_pins_cache()
    return pin

@app.post("/pins/{pin_id}/add_comment", response_model=PinResponse)
async def add_comment(
        pin_id: int,
        comment: str = Body(..., min_length=1, description="Содержание комментария"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Pin)
        .where(Pin.id == pin_id)
        .options(
            joinedload(Pin.author)
        )
    )
    pin = result.scalar_one_or_none()
    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")

    db.add(PinComments(pin_id=pin_id, comment=comment, user_id=current_user.id))

    await db.commit()
    await db.refresh(pin, attribute_names=["comments"])

    await invalidate_pins_cache()
    return PinResponse.model_validate(pin)


@app.get("/pins", response_model=PaginatedResponse[PinResponse])
@cache(expire=90, key_builder=pins_key_builder)
async def get_pins(
        page:int = Query(1, ge=1, description="Номер страницы"),
        size:int = Query(20, ge=1, le=100, description="Размер страницы"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    offset = (page - 1) * size

    query = select(Pin).options(
        selectinload(Pin.author),  # Загружаем автора сразу
        selectinload(Pin.comments)
    )

    query = query.order_by(Pin.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.limit(size).offset(offset)
    result = await db.execute(query)
    pins = result.scalars().all()

    liked_pin_ids = set()
    if current_user and pins:
        pin_ids = [pin.id for pin in pins]

        likes_result = await db.execute(
            select(PinLike.pin_id).where(
                (PinLike.pin_id.in_(pin_ids)) &
                (PinLike.user_id == current_user.id)
            )
        )
        liked_pin_ids = set(likes_result.scalars().all())

    for pin in pins:
        pin.is_liked = pin.id in liked_pin_ids

    total_pages = (total + size - 1) // size

    items = [PinResponse.model_validate(pin) for pin in pins]

    meta = PaginationMeta(
        page=page,
        size=size,
        total=total,
        pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

    return PaginatedResponse(items=items, meta=meta)

@app.get("/boards", response_model=List[BoardResponse])
async def get_boards(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    boards = (await db.execute(select(Board).where(Board.user_id == current_user.id).options(selectinload(Board.owner)))).scalars().all()

    return boards

@app.patch("/user/rename", response_model=UserProfile)
async def rename_user(
        new_name: str = Body(
            min_length=3,
            max_length=50,
            description="Новое имя пользователя",
            examples=["ruslan_dev", "user123"]
        ),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):

    check_new_name = (await db.execute(select(User).where(User.username == new_name))).scalar_one_or_none()

    if check_new_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Это имя уже занято"
        )

    current_user.username = new_name
    await db.commit()
    await db.refresh(current_user)

    await invalidate_pins_cache()

    return current_user

@app.patch("/user/change_description", response_model=UserProfile)
async def change_user_description(
        new_description: str = Body(
            description="Новое описание профиля"
        ),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    current_user.description = new_description
    await db.commit()
    await db.refresh(current_user)

    return current_user

@app.get("/user/me", response_model=UserProfile, tags=["User"])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

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
