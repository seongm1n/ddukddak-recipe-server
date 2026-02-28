from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.recipe import IngredientResponse


class AuthorResponse(BaseSchema):
    id: str
    name: str
    avatar_url: str | None = None


class FeedRecipeSummary(BaseSchema):
    id: str
    title: str
    thumbnail_url: str
    channel_name: str
    total_cost: int
    servings: int


class FeedRecipeDetail(BaseSchema):
    id: str
    title: str
    video_url: str
    thumbnail_url: str
    channel_name: str
    steps: list[str]
    ingredients: list[IngredientResponse]
    total_cost: int
    servings: int


class FeedItemResponse(BaseSchema):
    id: str
    recipe: FeedRecipeSummary
    author: AuthorResponse | None = None
    likes: int = 0
    created_at: datetime


class FeedDetailResponse(BaseSchema):
    id: str
    recipe: FeedRecipeDetail
    author: AuthorResponse | None = None
    likes: int = 0
    created_at: datetime
