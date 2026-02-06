from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
