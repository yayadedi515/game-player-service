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


def test_users_table_has_required_columns():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'users'
                """
            )
            rows = cursor.fetchall()

    column_names = {
        row[0]
        for row in rows
    }

    assert column_names == {
        "user_id",
        "username",
        "password_hash",
        "created_at"
    }


def test_players_have_nullable_owner_user_id_column():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'players'
                  AND column_name = 'owner_user_id'
                """
            )
            row = cursor.fetchone()

    assert row == ("integer", "YES")


def test_player_owner_references_users():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ccu.table_name,
                    ccu.column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.referential_constraints AS rc
                  ON rc.constraint_name = tc.constraint_name
                 AND rc.constraint_schema = tc.constraint_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.constraint_schema = tc.constraint_schema
                WHERE tc.constraint_schema = 'public'
                  AND tc.table_name = 'players'
                  AND tc.constraint_name =
                      'players_owner_user_id_fkey'
                  AND tc.constraint_type = 'FOREIGN KEY'
                """
            )
            row = cursor.fetchone()

    assert row == (
        "users",
        "user_id",
        "RESTRICT"
    )


def test_each_user_can_own_at_most_one_player():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.constraint_schema = tc.constraint_schema
                WHERE tc.constraint_schema = 'public'
                  AND tc.table_name = 'players'
                  AND tc.constraint_name =
                      'players_owner_user_id_key'
                  AND tc.constraint_type = 'UNIQUE'
                """
            )
            row = cursor.fetchone()

    assert row == ("owner_user_id",)
