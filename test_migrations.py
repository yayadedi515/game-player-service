from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from database import get_connection


BASE_DIR = Path(__file__).resolve().parent

pytestmark = [
    pytest.mark.integration,
    pytest.mark.usefixtures("reset_test_database")
]


def test_database_uses_latest_migration():
    alembic_config = Config(
        str(BASE_DIR / "alembic.ini")
    )
    migrations = ScriptDirectory.from_config(
        alembic_config
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT version_num FROM alembic_version"
            )
            row = cursor.fetchone()

    assert row is not None
    assert row[0] == migrations.get_current_head()


def test_transfer_history_foreign_keys_have_indexes():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = 'transfer_history'
                """
            )
            rows = cursor.fetchall()

    index_names = {
        row[0]
        for row in rows
    }

    assert "ix_transfer_history_sender_id" in index_names
    assert "ix_transfer_history_receiver_id" in index_names
