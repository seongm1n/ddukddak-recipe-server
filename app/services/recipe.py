import asyncio
import logging

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import status

from app.core.exceptions import AppException, NotFoundException
from app.models.recipe import Recipe
from app.repositories.recipe import RecipeRepository
from app.schemas.recipe import IngredientResponse, RecipeResponse
from app.services import gemini_analyzer, youtube

logger = logging.getLogger(__name__)


class RecipeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.recipe_repo = RecipeRepository(session)

    async def analyze(self, video_url: str, user_id: str) -> RecipeResponse:
        """유튜브 URL을 분석하여 레시피를 반환한다."""
        video_id = youtube.extract_video_id(video_url)

        # 캐시 확인
        cached = await self.recipe_repo.find_by_video_id(video_id)
        if cached:
            logger.info("Cache hit for video_id: %s", video_id)
            return self._to_response(cached)

        # YouTube 메타데이터 조회
        metadata = await asyncio.to_thread(youtube.fetch_video_metadata, video_id)

        # Gemini로 YouTube 영상 직접 분석
        analysis = await asyncio.to_thread(
            gemini_analyzer.analyze_recipe_from_video, video_url
        )

        # DB 저장 (캐시)
        ingredients_data = [
            {
                "name": ing.name,
                "quantity": ing.quantity,
                "unit": ing.unit,
                "price": ing.price,
                "note": ing.note,
            }
            for ing in analysis.ingredients
        ]

        try:
            recipe = await self.recipe_repo.create(
                video_id=video_id,
                video_url=video_url,
                title=metadata.title,
                thumbnail_url=metadata.thumbnail_url,
                channel_name=metadata.channel_name,
                steps=analysis.steps,
                total_cost=analysis.total_cost,
                servings=analysis.servings,
                ingredients_data=ingredients_data,
                analyzed_by=user_id,
            )
        except IntegrityError:
            await self.session.rollback()
            recipe = await self.recipe_repo.find_by_video_id(video_id)
            if recipe is None:
                raise AppException("레시피 분석 중 오류가 발생했습니다")

        return self._to_response(recipe)

    async def save(self, recipe_id: str, user_id: str) -> RecipeResponse:
        """레시피를 유저 컬렉션에 저장한다."""
        recipe = await self.recipe_repo.find_by_id(recipe_id)
        if not recipe:
            raise NotFoundException("레시피를 찾을 수 없습니다")

        try:
            saved = await self.recipe_repo.save_for_user(user_id, recipe_id)
        except IntegrityError:
            await self.session.rollback()
            raise AppException("이미 저장된 레시피입니다", status.HTTP_409_CONFLICT)

        stmt = (
            update(Recipe)
            .where(Recipe.id == recipe_id)
            .values(save_count=Recipe.save_count + 1)
        )
        await self.session.execute(stmt)
        await self.session.refresh(recipe)

        return self._to_response(recipe, saved_at=saved.created_at)

    async def list_saved(self, user_id: str) -> list[RecipeResponse]:
        """유저가 저장한 레시피 목록을 반환한다."""
        results = await self.recipe_repo.find_saved_by_user(user_id)
        return [self._to_response(recipe, saved_at=saved_at) for recipe, saved_at in results]

    async def delete_saved(self, recipe_id: str, user_id: str) -> None:
        """저장된 레시피를 삭제한다."""
        if not await self.recipe_repo.is_saved_by_user(user_id, recipe_id):
            raise NotFoundException("저장된 레시피가 아닙니다")

        await self.recipe_repo.delete_saved(user_id, recipe_id)

        stmt = (
            update(Recipe)
            .where(Recipe.id == recipe_id, Recipe.save_count > 0)
            .values(save_count=Recipe.save_count - 1)
        )
        await self.session.execute(stmt)

    def _to_response(self, recipe, saved_at=None) -> RecipeResponse:
        """Recipe 모델을 RecipeResponse로 변환한다."""
        return RecipeResponse(
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
            analyzed_by=recipe.analyzed_by,
            saved_at=saved_at,
        )
