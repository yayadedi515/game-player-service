from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenServiceProtocol(Protocol):
    def create_access_token(
            self,
            subject: str
    ) -> str:
        ...

    def decode_access_token(
            self,
            token: str
    ) -> str:
        ...
