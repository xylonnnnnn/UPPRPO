from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, StringConstraints


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

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None