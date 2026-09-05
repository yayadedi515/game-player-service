from user_exceptions import DuplicateUserError
from password_hasher_protocol import PasswordHasherProtocol
from user_repository_protocol import UserRepositoryProtocol

class UserService:
    def __init__(
            self,
            repository: UserRepositoryProtocol,
            password_hasher: PasswordHasherProtocol
    ):
        self.repository = repository
        self.password_hasher = password_hasher

    def register_user(
            self,
            username: str,
            plain_password: str
    ) -> dict:
        password_hash = (
            self.password_hasher.hash_password(
                plain_password
            )
        )

        user = self.repository.create_user(
            username,
            password_hash
        )
        if user is None:
            raise DuplicateUserError

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "created_at": user["created_at"]
        }
