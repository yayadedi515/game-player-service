from manage_users import main
from user_exceptions import UserNotFoundError


class FakeUserService:
    def __init__(self):
        self.promoted_username = None

    def promote_user_to_admin(self, username):
        self.promoted_username = username

        return {
            "user_id": 1,
            "username": username,
            "role": "admin",
            "created_at": None
        }


def test_promote_admin_command_returns_success(
        capsys
):
    service = FakeUserService()

    exit_code = main(
        [
            "promote-admin",
            "aooshiro"
        ],
        service
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert (
        service.promoted_username
        == "aooshiro"
    )
    assert (
        captured.out
        == "Promoted aooshiro to admin.\n"
    )
    assert captured.err == ""


def test_promote_admin_command_returns_error_when_user_missing(
        capsys
):
    class MissingUserService:
        def promote_user_to_admin(
                self,
                username
        ):
            raise UserNotFoundError

    exit_code = main(
        [
            "promote-admin",
            "missing-user"
        ],
        MissingUserService()
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert (
        captured.err
        == "User not found: missing-user\n"
    )
