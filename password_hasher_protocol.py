from typing import Protocol, runtime_checkable


@runtime_checkable
class PasswordHasherProtocol(Protocol):
    def hash_password(
            self,
            plain_password: str
    ) -> str:
        ...

    def verify_password(
            self,
            plain_password: str,
            password_hash: str
    ) -> bool:
        ...
