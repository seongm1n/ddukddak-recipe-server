from fastapi import APIRouter

from app.api import auth, feed, health, recipe

api_router = APIRouter(prefix="/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(recipe.router)
api_router.include_router(feed.router)
