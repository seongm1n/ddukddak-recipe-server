from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

DBSession = Annotated[AsyncSession, Depends(get_session)]

async def _get_current_user_id(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None:
        raise UnauthorizedException("토큰이 누락되었습니다")
    
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("유효하지 않은 토큰입니다")
    
    if payload.get("type") != "access":
        raise UnauthorizedException("엑세스 토큰이 아닙니다")
    
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("토큰에 사용자 정보가 없습니다")
    
    return user_id

CurrentUserId = Annotated[str, Depends(_get_current_user_id)]