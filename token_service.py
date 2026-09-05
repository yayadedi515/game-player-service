from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError


class TokenService:
    ALGORITHM = "HS256"

    def __init__(
            self,
            secret_key: str,
            expire_minutes: int
    ):
        self.secret_key = secret_key
        self.expire_minutes = expire_minutes

    def create_access_token(
            self,
            subject: str
    ) -> str:
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                minutes=self.expire_minutes
            )
        )

        return jwt.encode(
            {
                "sub": subject,
                "exp": expires_at
            },
            self.secret_key,
            algorithm=self.ALGORITHM
        )

    def decode_access_token(
            self,
            token: str
    ) -> str:
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.ALGORITHM]
        )

        subject = payload.get("sub")

        if not isinstance(subject, str) or subject == "":
            raise InvalidTokenError(
                "Token subject is missing"
            )

        return subject
