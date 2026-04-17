from datetime import datetime
from typing import Annotated, Optional, TypeVar, Generic, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, StringConstraints, computed_field


class UserCreate(BaseModel):
    email: EmailStr
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    password: Annotated[str, StringConstraints(min_length=6)]

class UserDelete(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    password: Annotated[str, StringConstraints(min_length=6)]

class UserPublic(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)

class VerifyEmail(BaseModel):
    email: EmailStr
    code: int

class Token(BaseModel):
    access_token: str
    token_type: str

class PinCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    board_id: int
    # image_width: Optional[int] = None
    # image_height: Optional[int] = None

class CommentsResponse(BaseModel):
    comment: str
    created_at: datetime
    user: UserPublic

    model_config = ConfigDict(from_attributes=True)

class PinResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    image_url: str
    # image_width: Optional[int]
    # image_height: Optional[int]
    # aspect_ratio: Optional[float]
    likes_count: int = 0
    is_liked: bool = False
    author: UserPublic
    comments: List[CommentsResponse]

    model_config = ConfigDict(from_attributes=True)

class BoardResponse(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_private: bool = False
    created_at: datetime
    owner: UserPublic

    model_config = ConfigDict(from_attributes=True)

class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_private: bool = False


class TokenData(BaseModel):
    username: Optional[str] = None

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы (начинается с 1)")
    size: int = Field(20, ge=1, le=100, description="Элементов на страницу (макс 100)")

class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int           # Всего записей в базе
    pages: int           # Всего страниц
    has_next: bool       # Есть ли следующая страница
    has_prev: bool       # Есть ли предыдущая страница

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]  # Список объектов (пинов)
    meta: PaginationMeta  # Метаданные

    model_config = ConfigDict(from_attributes=True)