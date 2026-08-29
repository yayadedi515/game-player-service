from enum import Enum


class TransferResult(Enum):
    SUCCESS = "success"
    PLAYER_NOT_FOUND = "player_not_found"
    INSUFFICIENT_SCORE = "insufficient_score"
    INVALID_REQUEST = "invalid_request"
