from password_hasher import PasswordHasher


def test_hash_password_does_not_return_plain_password():
    hasher = PasswordHasher()

    password_hash = hasher.hash_password(
        "koinucyanninaritai"
    )

    assert (
        password_hash
        != "koinucyanninaritai"
    )
    assert password_hash.startswith("$argon2")


def test_verify_password_accepts_matching_password():
    hasher = PasswordHasher()
    password_hash = hasher.hash_password(
        "rircyandaisuki"
    )

    result = hasher.verify_password(
        "rircyandaisuki",
        password_hash
    )

    assert result is True


def test_verify_password_rejects_wrong_password():
    hasher = PasswordHasher()
    password_hash = hasher.hash_password(
        "quanniangsekaiichi"
    )

    result = hasher.verify_password(
        "哈基米那没路躲",
        password_hash
    )

    assert result is False


def test_same_password_creates_different_hashes():
    hasher = PasswordHasher()

    first_hash = hasher.hash_password(
        "qishimaoniangyehaixing"
    )
    second_hash = hasher.hash_password(
        "qishimaoniangyehaixing"
    )

    assert first_hash != second_hash
    assert hasher.verify_password(
        "qishimaoniangyehaixing",
        first_hash
    )
    assert hasher.verify_password(
        "qishimaoniangyehaixing",
        second_hash
    )
