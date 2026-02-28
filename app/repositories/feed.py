from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recipe import Recipe
from app.models.user import User


class FeedRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_all_paginated(
        self, sort: str, page: int, limit: int
    ) -> list[tuple[Recipe, User | None]]:
        """피드 목록을 페이지네이션하여 조회한다."""
        offset = (page - 1) * limit

        stmt = (
            select(Recipe, User)
            .outerjoin(User, Recipe.analyzed_by == User.id)
            .options(selectinload(Recipe.ingredients))
            .offset(offset)
            .limit(limit)
        )

        if sort == "popular":
            stmt = stmt.order_by(Recipe.save_count.desc(), Recipe.created_at.desc())
        else:
            stmt = stmt.order_by(Recipe.created_at.desc())

        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def find_by_id(
        self, recipe_id: str
    ) -> tuple[Recipe, User | None] | None:
        """레시피 ID로 피드 상세를 조회한다."""
        stmt = (
            select(Recipe, User)
            .outerjoin(User, Recipe.analyzed_by == User.id)
            .where(Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients))
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        return (row[0], row[1])
