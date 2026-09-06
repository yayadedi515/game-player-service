import argparse
import sys

from user_exceptions import UserNotFoundError
from password_hasher import PasswordHasher
from user_repository import UserRepository
from user_service import UserService


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage login users"
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    promote_parser = subparsers.add_parser(
        "promote-admin",
        help="Promote an existing user to admin"
    )
    promote_parser.add_argument("username")

    return parser


def create_user_service() -> UserService:
    return UserService(
        UserRepository(),
        PasswordHasher()
    )


def main(
        argv=None,
        service=None
) -> int:
    parser = create_parser()
    arguments = parser.parse_args(argv)

    if service is None:
        service = create_user_service()

    try:
        user = service.promote_user_to_admin(
            arguments.username
        )
    except UserNotFoundError:
        print(
            (
                "User not found: "
                f"{arguments.username}"
            ),
            file=sys.stderr
        )
        return 1

    print(
        f"Promoted {user['username']} to admin."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
