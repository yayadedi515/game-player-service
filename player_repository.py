from database import get_connection
from psycopg.errors import UniqueViolation

def find_player_by_name(name: str) -> dict | None:
    cleaned_name = name.strip()

    if cleaned_name == "":
        return None

    query = """
        SELECT player_id, name, score, created_at
        FROM players
        WHERE name = %s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (cleaned_name,))
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "player_id": row[0],
        "name": row[1],
        "score": row[2],
        "created_at": row[3]
    }


def create_player(name: str) -> dict | None:
    cleaned_name = name.strip()

    if cleaned_name == "":
        return None

    query = """
        INSERT INTO players (name)
        VALUES (%s)
        RETURNING player_id, name, score, created_at
    """

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (cleaned_name,))
                row = cursor.fetchone()

    except UniqueViolation:
        return None

    if row is None:
        return None

    return {
        "player_id": row[0],
        "name": row[1],
        "score": row[2],
        "created_at": row[3]
    }


def add_score(name: str, score: int) -> dict | None:
    cleaned_name = name.strip()

    if cleaned_name == "" or score < 0:
        return None

    query = """
        UPDATE players set score = score + %s WHERE name = %s
        RETURNING player_id, name, score, created_at
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (score, cleaned_name,))
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "player_id": row[0],
        "name": row[1],
        "score": row[2],
        "created_at": row[3]
    }


def get_ranking() -> list[dict]:
    query = """
        SELECT player_id, name, score, created_at
        FROM players
        ORDER BY score DESC, name ASC
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(
                {"player_id": row[0], "name": row[1],
                 "score": row[2], "created_at": row[3]
                }
            )
        return result
