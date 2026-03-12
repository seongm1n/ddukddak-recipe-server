"""인메모리 refresh token 저장소.

서버 재시작 시 초기화되며, 이후 Redis/DB로 교체 가능.
"""


class TokenStore:
    def __init__(self) -> None:
        # token -> user_id
        self._tokens: dict[str, str] = {}

    def save(self, token: str, user_id: str) -> None:
        self._tokens[token] = user_id

    def verify(self, token: str) -> str | None:
        """토큰이 유효하면 user_id를 반환한다."""
        return self._tokens.get(token)

    def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)

    def revoke_all(self, user_id: str) -> None:
        """해당 유저의 모든 refresh token을 삭제한다."""
        self._tokens = {
            t: uid for t, uid in self._tokens.items() if uid != user_id
        }


token_store = TokenStore()
