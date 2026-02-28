import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.nickname import generate_nickname
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.repositories.user import UserRepository
from app.schemas.auth import LoginResponse, TokenResponse, UserResponse
from app.services.social_auth import verify_social_token


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def login(self, provider: str, token: str) -> LoginResponse:
        social_user = await verify_social_token(provider, token)

        user = await self.user_repo.find_by_provider_and_provider_id(
            provider, social_user.provider_id
        )

        if user is None:
            try:
                user = await self.user_repo.create(
                    provider=provider,
                    provider_id=social_user.provider_id,
                    name=generate_nickname(),
                    email=social_user.email,
                    avatar_url=social_user.avatar_url,
                )
            except IntegrityError:
                await self.session.rollback()
                user = await self.user_repo.find_by_provider_and_provider_id(
                    provider, social_user.provider_id
                )
                if user is None:
                    raise UnauthorizedException("로그인 처리 중 오류가 발생했습니다")

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=create_access_token(user.id),
                refresh_token=create_refresh_token(user.id),
            ),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("리프레시 토큰이 만료되었습니다")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("유효하지 않은 리프레시 토큰입니다")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("리프레시 토큰이 아닙니다")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("토큰에 사용자 정보가 없습니다")

        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise UnauthorizedException("존재하지 않는 사용자입니다")

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_me(self, user_id: str) -> UserResponse:
        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise UnauthorizedException("존재하지 않는 사용자입니다")
        return UserResponse.model_validate(user)
