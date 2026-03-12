import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.nickname import generate_nickname
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.token_store import token_store
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

        refresh = create_refresh_token(user.id)
        token_store.save(refresh, user.id)

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=create_access_token(user.id),
                refresh_token=refresh,
            ),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        if token_store.verify(refresh_token) is None:
            raise UnauthorizedException("유효하지 않은 리프레시 토큰입니다")

        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            token_store.revoke(refresh_token)
            raise UnauthorizedException("리프레시 토큰이 만료되었습니다")
        except jwt.InvalidTokenError:
            token_store.revoke(refresh_token)
            raise UnauthorizedException("유효하지 않은 리프레시 토큰입니다")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("리프레시 토큰이 아닙니다")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("토큰에 사용자 정보가 없습니다")

        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise UnauthorizedException("존재하지 않는 사용자입니다")

        # 기존 토큰 삭제 + 새 토큰 저장
        token_store.revoke(refresh_token)
        new_refresh = create_refresh_token(user.id)
        token_store.save(new_refresh, user.id)

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=new_refresh,
        )

    def logout(self, refresh_token: str, user_id: str) -> None:
        owner = token_store.verify(refresh_token)
        if owner != user_id:
            raise UnauthorizedException("유효하지 않은 리프레시 토큰입니다")
        token_store.revoke(refresh_token)

    async def get_me(self, user_id: str) -> UserResponse:
        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise UnauthorizedException("존재하지 않는 사용자입니다")
        return UserResponse.model_validate(user)

    async def delete_account(self, user_id: str) -> None:
        """사용자 계정과 관련 데이터를 삭제한다."""
        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise UnauthorizedException("존재하지 않는 사용자입니다")
        token_store.revoke_all(user_id)
        await self.user_repo.delete(user_id)
