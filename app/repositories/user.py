from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import UserSavedRecipe, Recipe
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_provider_and_provider_id(
            self, provider: str, provider_id: str,
    ) -> User | None:
        stmt = select(User).where(
            User.provider == provider,
            User.provider_id == provider_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str) -> User | None:
        return await self.session.get(User, user_id)

    async def create(
            self,
            provider: str,
            provider_id: str,
            name: str,
            email: str | None = None,
            avatar_url: str | None = None,
    ) -> User:
        user = User(
            provider=provider,
            provider_id=provider_id,
            name=name,
            email=email,
            avatar_url=avatar_url,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def delete(self, user_id: str) -> None:
        """사용자 계정과 관련 데이터를 삭제한다."""
        # 저장된 레시피 연결 해제
        await self.session.execute(
            delete(UserSavedRecipe).where(UserSavedRecipe.user_id == user_id)
        )

        # analyzed_by NULL 처리
        await self.session.execute(
            update(Recipe).where(Recipe.analyzed_by == user_id).values(analyzed_by=None)
        )

        # 사용자 삭제
        user = await self.session.get(User, user_id)
        if user:
            await self.session.delete(user)
            await self.session.flush()
