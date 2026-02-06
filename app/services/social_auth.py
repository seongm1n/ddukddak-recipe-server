from dataclasses import dataclass

import httpx
import jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException

settings = get_settings()

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

@dataclass(frozen=True)
class SocialUserInfo:
    provider_id: str
    email: str | None = None
    avatar_url: str | None = None

async def verify_apple_token(token: str) -> SocialUserInfo:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(APPLE_JWKS_URL)
        jwks = resp.json()

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    key = None
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
            break

    if key is None:
        raise UnauthorizedException("Apple 공개키를 찾을 수 없습니다")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.apple_client_id,
            issuer="https://appleid.apple.com",
        )
    except jwt.PyJWTError:
        raise UnauthorizedException("유효하지 않은 Apple 토큰입니다")

    provider_id = payload.get("sub")
    if provider_id is None:
        raise UnauthorizedException("Apple 토큰에 사용자 정보가 없습니다")

    return SocialUserInfo(
        provider_id=provider_id,
        email=payload.get("email"),
    )

async def verify_google_token(token: str) -> SocialUserInfo:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            GOOGLE_TOKEN_INFO_URL, params={"id_token": token}
        )

    if resp.status_code != 200:
        raise UnauthorizedException("유효하지 않은 Google 토큰입니다")

    payload = resp.json()

    if payload.get("aud") != settings.google_client_id:
        raise UnauthorizedException("Google 클라이언트 ID가 일치하지 않습니다")

    provider_id = payload.get("sub")
    if provider_id is None:
        raise UnauthorizedException("Google 토큰에 사용자 정보가 없습니다")

    return SocialUserInfo(
        provider_id=provider_id,
        email=payload.get("email"),
        avatar_url=payload.get("picture"),
    )

async def verify_kakao_token(token: str) -> SocialUserInfo:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            KAKAO_USER_INFO_URL,
            headers={"Authorization": f"Bearer {token}"},
        )

    if resp.status_code != 200:
        raise UnauthorizedException("유효하지 않은 Kakao 토큰입니다")

    data = resp.json()
    account = data.get("kakao_account", {})
    profile = account.get("profile", {})

    kakao_id = data.get("id")
    if kakao_id is None:
        raise UnauthorizedException("Kakao 토큰에 사용자 정보가 없습니다")

    return SocialUserInfo(
        provider_id=str(kakao_id),
        email=account.get("email"),
        avatar_url=profile.get("profile_image_url"),
    )

PROVIDER_VERIFIERS = {
    "apple": verify_apple_token,
    "google": verify_google_token,
    "kakao": verify_kakao_token,
}

async def verify_social_token(provider: str, token: str) -> SocialUserInfo:
    verifier = PROVIDER_VERIFIERS.get(provider)
    if verifier is None:
        raise UnauthorizedException(f"지원하지 않는 프로바이더: {provider}")
    return await verifier(token)
