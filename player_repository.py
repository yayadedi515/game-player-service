from psycopg.errors import UniqueViolation

from database import get_connection
from transfer_result import TransferResult


def _find_player_by_name(name: str) -> dict | None:
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


def _create_player(name: str) -> dict | None:
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


def _add_score(name: str, score: int) -> dict | None:
    cleaned_name = name.strip()

    if cleaned_name == "" or score < 0:
        return None

    query = """
        UPDATE players
        SET score = score + %s
        WHERE name = %s
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


def _get_ranking() -> list[dict]:
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
            result.append({
                "player_id": row[0],
                "name": row[1],
                "score": row[2],
                "created_at": row[3]
            })
        return result


def _transfer_score(
        sender: str,
        receiver: str,
        points: int
) -> TransferResult:
    cleaned_sender = sender.strip()
    cleaned_receiver = receiver.strip()

    if (
            not cleaned_sender
            or not cleaned_receiver
            or cleaned_sender == cleaned_receiver
            or points <= 0
    ):
        return TransferResult.INVALID_REQUEST

    select_query = """
        SELECT player_id, name, score
        FROM players
        WHERE name IN (%s, %s)
        ORDER BY player_id
        FOR UPDATE
    """

    subtract_query = """
        UPDATE players
        SET score = score - %s
        WHERE player_id = %s
    """

    add_query = """
        UPDATE players
        SET score = score + %s
        WHERE player_id = %s
    """

    history_query = """
        INSERT INTO transfer_history (sender_id, receiver_id, points)
        VALUES (%s, %s, %s)
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                select_query,
                (cleaned_sender, cleaned_receiver),
            )
            rows = cursor.fetchall()

            if len(rows) != 2:
                return TransferResult.PLAYER_NOT_FOUND

            locked_players = {
                row[1]: row
                for row in rows
            }

            sender_row = locked_players[cleaned_sender]
            receiver_row = locked_players[cleaned_receiver]

            if sender_row[2] < points:
                return TransferResult.INSUFFICIENT_SCORE

            cursor.execute(
                subtract_query,
                (points, sender_row[0]),
            )
            cursor.execute(
                add_query,
                (points, receiver_row[0]),
            )
            cursor.execute(
                history_query,
                (sender_row[0], receiver_row[0], points),
            )

    return TransferResult.SUCCESS


def _get_transfer_history(
        limit: int = 20,
        offset: int = 0
) -> list[dict]:
    if (
            limit < 1
            or limit > 100
            or offset < 0
    ):
        raise ValueError(
            "Invalid pagination parameters"
        )

    query = """
        SELECT
            history.transfer_id,
            sender.name,
            receiver.name,
            history.points,
            history.created_at
        FROM transfer_history AS history
        JOIN players AS sender
            ON sender.player_id = history.sender_id
        JOIN players AS receiver
            ON receiver.player_id = history.receiver_id
        ORDER BY history.transfer_id DESC
        LIMIT %s
        OFFSET %s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (limit, offset)
            )
            rows = cursor.fetchall()

    result = []

    for row in rows:
        result.append({
            "transfer_id": row[0],
            "sender": row[1],
            "receiver": row[2],
            "points": row[3],
            "created_at": row[4]
        })

    return result


def _delete_player(name: str) -> dict | None:
    cleaned_name = name.strip()

    if cleaned_name == "":
        return None

    query = """
        DELETE FROM players
        WHERE name = %s
        RETURNING player_id, name, score, created_at
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


class PlayerRepository:
    def find_player_by_name(self, name):
        return _find_player_by_name(name)

    def create_player(self, name):
        return _create_player(name)

    def add_score(self, name, score):
        return _add_score(name, score)

    def get_ranking(self):
        return _get_ranking()

    def transfer_score(self, sender, receiver, points):
        return _transfer_score(
            sender,
            receiver,
            points
        )

    def delete_player(self, name):
        return _delete_player(name)

    def get_transfer_history(
            self,
            limit=20,
            offset=0
    ):
        return _get_transfer_history(
            limit=limit,
            offset=offset
        )
