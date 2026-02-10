from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.feed import FeedRepository
from app.schemas.feed import (
    AuthorResponse,
    FeedDetailResponse,
    FeedItemResponse,
    FeedRecipeDetail,
    FeedRecipeSummary,
)
from app.schemas.recipe import IngredientResponse


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self.feed_repo = FeedRepository(session)

    async def list_feed(
            self, sort: str, page: int, limit: int
    ) -> list[FeedItemResponse]:
        """피드 목록을 조회한다."""
        results = await self.feed_repo.find_all_paginated(sort, page, limit)
        return [self._to_feed_item(recipe, user) for recipe, user in results]
    
    async def get_feed_detail(self, recipe_id: str) -> FeedDetailResponse:
        """피드 상세를 조회한다."""
        result = await self.feed_repo.find_by_id(recipe_id)
        if result is None:
            raise NotFoundException("레시피를 찾을 수 없습니다")
        
        recipe, user = result
        return self._to_feed_detail(recipe, user)
    
    def _to_feed_item(self, recipe, user) -> FeedItemResponse:
        """목록용 응답으로 변환한다."""
        return FeedItemResponse(
            id=recipe.id,
            recipe=FeedRecipeSummary(
                id=recipe.id,
                title=recipe.title,
                thumbnail_url=recipe.thumbnail_url,
                channel_name=recipe.channel_name,
                total_cost=recipe.total_cost,
                servings=recipe.servings,
            ),
            author=self._to_author(user),
            likes=recipe.save_count,
            created_at=recipe.created_at,
        )
    
    def _to_feed_detail(self, recipe, user) -> FeedDetailResponse:
        """상세용 응답으로 변환한다."""
        return FeedDetailResponse(
            id=recipe.id,
            recipe=FeedRecipeDetail(
                id=recipe.id,
                title=recipe.title,
                video_url=recipe.video_url,
                thumbnail_url=recipe.thumbnail_url,
                channel_name=recipe.channel_name,
                steps=recipe.steps,
                ingredients=[
                    IngredientResponse(
                        id=ing.id,
                        name=ing.name,
                        quantity=ing.quantity,
                        unit=ing.unit,
                        price=ing.price,
                        note=ing.note,
                    )
                    for ing in sorted(recipe.ingredients, key=lambda x: x.display_order)
                ],
                total_cost=recipe.total_cost,
                servings=recipe.servings,
            ),
            author=self._to_author(user),
            likes=recipe.save_count,
            created_at=recipe.created_at,
        )
    
    def _to_author(self, user) -> AuthorResponse | None:
        """User 모델을 AuthorResponse로 변환한다."""
        if user is None:
            return None
        return AuthorResponse(
            id=user.id,
            name=user.name,
            avatar_url=user.avatar_url,
        )