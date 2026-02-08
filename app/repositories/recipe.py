from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recipe import Ingredient, Recipe, UserSavedRecipe


class RecipeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_video_id(self, video_id: str) -> Recipe | None:
        """video_id로 캐시된 레시피를 조회한."""
        stmt = (
            select(Recipe)
            .where(Recipe.video_id == video_id)
            .options(selectinload(Recipe.ingredients))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_id(self, recipe_id: str) -> Recipe | None:
        """ID로 레시피를 조회한다."""
        stmt = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(
            self,
            video_id: str,
            video_url: str,
            title: str,
            thumbnail_url: str,
            channel_name: str,
            steps: list[str],
            total_cost: int,
            servings: int,
            ingredients_data: list[dict],
    ) -> Recipe:
        """레시피와 재료를 함께 생성한다."""
        recipe = Recipe(
            video_id=video_id,
            video_url=video_url,
            title=title,
            thumbnail_url=thumbnail_url,
            channel_name=channel_name,
            steps=steps,
            total_cost=total_cost,
            servings=servings,
        )
        self.session.add(recipe)
        await self.session.flush()

        for idx, ing in enumerate(ingredients_data):
            ingredient = Ingredient(
                recipe_id=recipe.id,
                name=ing["name"],
                quantity=ing["quantity"],
                unit=ing["unit"],
                price=ing["price"],
                note=ing.get("note"),
                display_order=idx,
            )
            self.session.add(ingredient)

        await self.session.flush()
        await self.session.refresh(recipe, ["ingredients"])
        return recipe
    
    async def find_saved_by_user(self, user_id: str) -> list[Recipe]:
        """유저가 저장한 레시피 목록을 조회한다."""
        stmt = (
            select(Recipe)
            .join(UserSavedRecipe)
            .where(UserSavedRecipe.user_id == user_id)
            .options(selectinload(Recipe.ingredients))
            .order_by(UserSavedRecipe.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def save_for_user(self, user_id: str, recipe_id: str) -> UserSavedRecipe:
        """유저의 컬렉션에 레시피를 저장한다."""
        saved = UserSavedRecipe(user_id=user_id, recipe_id=recipe_id)
        self.session.add(saved)
        await self.session.flush()
        return saved
    
    async def is_saved_by_user(self, user_id: str, recipe_id: str) -> bool:
        """유저가 이미 저장한 레시피인지 확인한다."""
        stmt = select(UserSavedRecipe).where(
            and_(
                UserSavedRecipe.user_id == user_id,
                UserSavedRecipe.recipe_id == recipe_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def delete_saved(self, user_id: str, recipe_id: str) -> None:
        """유저의 저장된 레시피를 삭제한다."""
        stmt = select(UserSavedRecipe).where(
            and_(
                UserSavedRecipe.user_id == user_id,
                UserSavedRecipe.recipe_id == recipe_id,
            )
        )
        result = await self.session.execute(stmt)
        saved = result.scalar_one_or_none()
        if saved:
            await self.session.delete(saved)
            await self.session.flush()
