import psycopg

from settings import get_settings


def get_connection():
    settings = get_settings()

    return psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=(
            settings.db_password
            .get_secret_value()
        )
    )
