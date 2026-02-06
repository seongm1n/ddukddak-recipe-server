from fastapi import APIRouter

from app.api import health

api_router = APIRouter(prefix="/v1")

api_router.include_router(health.router)
