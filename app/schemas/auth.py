from datetime import datetime
from typing import Literal

from app.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    provider: Literal["apple", "google", "kakao"]
    token: str

class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str

class RefreshRequest(BaseSchema):
    refresh_token: str

class UserResponse(BaseSchema):
    id: str
    email: str | None = None
    name: str
    avatar_url: str | None = None
    provider: str
    created_at: datetime

class LoginResponse(BaseSchema):
    user: UserResponse
    tokens: TokenResponse
