from fastapi import APIRouter

from app.core.dependencies import CurrentUserId, DBSession
from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest, TokenResponse, UserResponse
from app.schemas.base import ApiResponse, ok

from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(body: LoginRequest, session: DBSession) -> ApiResponse[LoginResponse]:
    service = AuthService(session)
    result = await service.login(body.provider, body.token)
    return ok(result)

@router.post("/logout")
async def logout(body: RefreshRequest, _user_id: CurrentUserId, session: DBSession) -> ApiResponse[None]:
    service = AuthService(session)
    service.logout(body.refresh_token)
    return ok(None)

@router.post("/refresh")
async def refresh(body: RefreshRequest, session: DBSession) -> ApiResponse[TokenResponse]:
    service = AuthService(session)
    result = await service.refresh(body.refresh_token)
    return ok(result)

@router.get("/me")
async def get_me(user_id: CurrentUserId, session: DBSession) -> ApiResponse[UserResponse]:
    service = AuthService(session)
    result = await service.get_me(user_id)
    return ok(result)

@router.delete("/me")
async def delete_account(user_id: CurrentUserId, session: DBSession) -> ApiResponse[None]:
    service = AuthService(session)
    await service.delete_account(user_id)
    return ok(None)
