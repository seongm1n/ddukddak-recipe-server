from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserId, DBSession
from app.schemas.base import ApiResponse, ok
from app.schemas.recipe import AnalyzeRequest, RecipeResponse, SaveRequest
from app.services.recipe import RecipeService

router = APIRouter(prefix="/recipe", tags=["recipe"])


@router.post("/analyze")
async def analyze_recipe(
    body: AnalyzeRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> ApiResponse[RecipeResponse]:
    service = RecipeService(session)
    result = await service.analyze(body.video_url)
    return ok(result)


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_recipe(
    body: SaveRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> ApiResponse[RecipeResponse]:
    service = RecipeService(session)
    result = await service.save(body.recipe_id, user_id)
    return ok(result)


@router.get("/list")
async def list_recipes(
    user_id: CurrentUserId,
    session: DBSession,
) -> ApiResponse[list[RecipeResponse]]:
    service = RecipeService(session)
    result = await service.list_saved(user_id)
    return ok(result)


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    user_id: CurrentUserId,
    session: DBSession,
) -> ApiResponse[None]:
    service = RecipeService(session)
    await service.delete_saved(recipe_id, user_id)
    return ok(None)
