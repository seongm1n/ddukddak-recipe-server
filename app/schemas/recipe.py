from datetime import datetime

from app.schemas.base import BaseSchema


class AnalyzeRequest(BaseSchema):
    video_url: str


class SaveRequest(BaseSchema):
    recipe_id: str


class IngredientResponse(BaseSchema):
    id: str
    name: str
    quantity: str
    unit: str
    price: int
    note: str | None = None


class RecipeResponse(BaseSchema):
    id: str
    title: str
    video_url: str
    thumbnail_url: str
    channel_name: str
    steps: list[str]
    ingredients: list[IngredientResponse]
    total_cost: int
    servings: int
    analyzed_by: str | None = None
    saved_at: datetime | None = None
    