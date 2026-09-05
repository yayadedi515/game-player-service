import pytest
from jwt import InvalidTokenError

from user_exceptions import InvalidAccessTokenError
from pydantic import SecretStr

from token_service import TokenService

from dependencies import (
    get_player_repository,
    get_player_service,
    get_redis_client,
    get_ranking_cache,
    get_user_repository,
    get_password_hasher,
    get_user_service,
    get_token_service,
    get_current_user,
)
from player_service import PlayerService
from player_repository import PlayerRepository
from player_repository_protocol import PlayerRepositoryProtocol
from ranking_cache import RedisRankingCache
from password_hasher import PasswordHasher
from user_repository import UserRepository
from user_service import UserService
from password_hasher_protocol import PasswordHasherProtocol
from user_repository_protocol import UserRepositoryProtocol

class FakeSettings:
    redis_host = "cache"
    redis_port = 6380
    ranking_cache_ttl_seconds = 120
    redis_timeout_seconds = 0.5


def test_get_player_repository_returns_player_repository():
    repository = get_player_repository()

    assert isinstance(repository, PlayerRepository)
    assert isinstance(repository, PlayerRepositoryProtocol)


def test_get_player_service_uses_provided_dependencies():
    repository = PlayerRepository()
    ranking_cache = object()

    service = get_player_service(
        repository,
        ranking_cache
    )

    assert isinstance(service, PlayerService)
    assert service.repository is repository
    assert service.ranking_cache is ranking_cache


def test_get_redis_client_uses_provided_settings():
    redis_client = get_redis_client(
        FakeSettings()
    )

    connection_settings = (
        redis_client
        .connection_pool
        .connection_kwargs
    )

    assert connection_settings["host"] == "cache"
    assert connection_settings["port"] == 6380
    assert (
        connection_settings["decode_responses"]
        is True
    )
    assert (
            connection_settings["socket_connect_timeout"]
            == 0.5
    )
    assert (
            connection_settings["socket_timeout"]
            == 0.5
    )
    assert (
            connection_settings["retry"].get_retries()
            == 0
    )


def test_get_ranking_cache_uses_client_and_ttl():
    redis_client = object()

    cache = get_ranking_cache(
        redis_client,
        FakeSettings()
    )

    assert isinstance(cache, RedisRankingCache)
    assert cache.redis_client is redis_client
    assert cache.ttl_seconds == 120


def test_get_user_repository_returns_user_repository():
    repository = get_user_repository()

    assert isinstance(repository, UserRepository)
    assert isinstance(
        repository,
        UserRepositoryProtocol
    )


def test_get_password_hasher_returns_password_hasher():
    password_hasher = get_password_hasher()

    assert isinstance(
        password_hasher,
        PasswordHasher
    )
    assert isinstance(
        password_hasher,
        PasswordHasherProtocol
    )


def test_get_user_service_uses_provided_dependencies():
    repository = UserRepository()
    password_hasher = PasswordHasher()

    service = get_user_service(
        repository,
        password_hasher
    )

    assert isinstance(service, UserService)
    assert service.repository is repository
    assert service.password_hasher is password_hasher


def test_get_token_service_uses_jwt_settings():
    class FakeTokenSettings:
        jwt_secret_key = SecretStr(
            "test-secret-key-at-least-32-characters"
        )
        access_token_expire_minutes = 45

    service = get_token_service(
        FakeTokenSettings()
    )

    assert isinstance(service, TokenService)
    assert (
        service.secret_key
        == "test-secret-key-at-least-32-characters"
    )
    assert service.expire_minutes == 45


def test_get_current_user_decodes_token_and_loads_user():
    class FakeTokenService:
        def __init__(self):
            self.decoded_token = None

        def decode_access_token(self, token):
            self.decoded_token = token
            return "aooshiro"

    class FakeUserRepository:
        def __init__(self):
            self.requested_username = None

        def find_user_by_username(self, username):
            self.requested_username = username
            return {
                "user_id": 1,
                "username": "aooshiro",
                "password_hash": "stored-password-hash",
                "created_at": None
            }

    token_service = FakeTokenService()
    repository = FakeUserRepository()

    user = get_current_user(
        "signed-access-token",
        token_service,
        repository
    )

    assert (
        token_service.decoded_token
        == "signed-access-token"
    )
    assert (
        repository.requested_username
        == "aooshiro"
    )
    assert user == {
        "user_id": 1,
        "username": "aooshiro",
        "created_at": None
    }
    assert "password_hash" not in user


def test_get_current_user_rejects_invalid_token():
    class FakeTokenService:
        def decode_access_token(self, token):
            raise InvalidTokenError(
                "Invalid token"
            )

    class FakeUserRepository:
        def find_user_by_username(self, username):
            raise AssertionError(
                "Repository must not be called"
            )

    with pytest.raises(InvalidAccessTokenError):
        get_current_user(
            "invalid-token",
            FakeTokenService(),
            FakeUserRepository()
        )


def test_get_current_user_rejects_missing_user():
    class FakeTokenService:
        def decode_access_token(self, token):
            return "deleted-user"

    class FakeUserRepository:
        def find_user_by_username(self, username):
            return None

    with pytest.raises(InvalidAccessTokenError):
        get_current_user(
            "valid-token",
            FakeTokenService(),
            FakeUserRepository()
        )
