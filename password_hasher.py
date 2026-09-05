from pwdlib import PasswordHash


class PasswordHasher:
    def __init__(self):
        self.password_hash = (
            PasswordHash.recommended()
        )

    def hash_password(
            self,
            plain_password: str
    ) -> str:
        return self.password_hash.hash(
            plain_password
        )

    def verify_password(
            self,
            plain_password: str,
            password_hash: str
    ) -> bool:
        return self.password_hash.verify(
            plain_password,
            password_hash
        )
