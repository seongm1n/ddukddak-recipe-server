from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserId, DBSession
from app.schemas.base import ApiResponse, ok
from app.schemas.feed import FeedDetailResponse, FeedItemResponse
from app.services.feed import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("")
async def list_feed(
    user_id: CurrentUserId,
    session: DBSession,
    sort: str = Query("latest", pattern="^(latest|popular)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
) -> ApiResponse[list[FeedItemResponse]]:
    service = FeedService(session)
    result = await service.list_feed(sort, page, limit)
    return ok(result)


@router.get("/{recipe_id}")
async def get_feed_detail(
    recipe_id: str,
    user_id: CurrentUserId,
    session: DBSession,
) -> ApiResponse[FeedDetailResponse]:
    service = FeedService(session)
    result = await service.get_feed_detail(recipe_id)
    return ok(result)
