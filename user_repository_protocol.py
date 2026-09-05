from typing import Protocol, runtime_checkable


@runtime_checkable
class UserRepositoryProtocol(Protocol):
    def create_user(
            self,
            username: str,
            password_hash: str
    ) -> dict | None:
        ...

    def find_user_by_username(
            self,
            username: str
    ) -> dict | None:
        ...
