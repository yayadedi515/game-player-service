import database
from settings import Settings


def test_get_connection_uses_validated_settings(
        monkeypatch
):
    settings = Settings(
        db_host="database",
        db_port=5432,
        db_name="test_database",
        db_user="postgres",
        db_password="secret",
        _env_file=None
    )
    expected_connection = object()
    received_arguments = {}

    def fake_connect(**arguments):
        received_arguments.update(arguments)
        return expected_connection

    monkeypatch.setattr(
        database,
        "get_settings",
        lambda: settings
    )
    monkeypatch.setattr(
        database.psycopg,
        "connect",
        fake_connect
    )

    connection = database.get_connection()

    assert connection is expected_connection
    assert received_arguments == {
        "host": "database",
        "port": 5432,
        "dbname": "test_database",
        "user": "postgres",
        "password": "secret"
    }