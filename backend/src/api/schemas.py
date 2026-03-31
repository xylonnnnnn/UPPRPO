from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, StringConstraints, computed_field


class UserCreate(BaseModel):
    email: EmailStr
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    password: Annotated[str, StringConstraints(min_length=6)]

class UserDelete(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    password: Annotated[str, StringConstraints(min_length=6)]

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
    author_username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BoardResponse(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_private: bool = False
    created_at: datetime
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_private: bool = False


class TokenData(BaseModel):
    username: Optional[str] = None