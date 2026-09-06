import pytest

from manage_users import main
from user_repository import UserRepository


pytestmark = [
    pytest.mark.integration,
    pytest.mark.usefixtures(
        "reset_test_database"
    )
]


def test_promote_admin_command_updates_postgresql(
        capsys
):
    repository = UserRepository()
    repository.create_user(
        "aooshiro",
        "stored-password-hash"
    )

    exit_code = main(
        [
            "promote-admin",
            "aooshiro"
        ]
    )

    promoted_user = (
        repository.find_user_by_username(
            "aooshiro"
        )
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert promoted_user["role"] == "admin"
    assert (
        captured.out
        == "Promoted aooshiro to admin.\n"
    )
    assert captured.err == ""
