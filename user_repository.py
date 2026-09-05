from database import get_connection


class UserRepository:
    def create_user(
            self,
            username: str,
            password_hash: str
    ) -> dict | None:
        cleaned_username = username.strip()

        if cleaned_username == "":
            return None

        query = """
            INSERT INTO users (
                username,
                password_hash
            )
            VALUES (%s, %s)
            ON CONFLICT (username) DO NOTHING
            RETURNING
                user_id,
                username,
                password_hash,
                created_at
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        cleaned_username,
                        password_hash
                    )
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return {
            "user_id": row[0],
            "username": row[1],
            "password_hash": row[2],
            "created_at": row[3]
        }

    def find_user_by_username(
            self,
            username: str
    ) -> dict | None:
        cleaned_username = username.strip()

        if cleaned_username == "":
            return None

        query = """
            SELECT
                user_id,
                username,
                password_hash,
                created_at
            FROM users
            WHERE username = %s
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (cleaned_username,)
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return {
            "user_id": row[0],
            "username": row[1],
            "password_hash": row[2],
            "created_at": row[3]
        }
