from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    model_validator
)


PlayerName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=50
    )
]


class PlayerCreate(BaseModel):
    name: PlayerName


class ScoreAdd(BaseModel):
    points: int = Field(ge=0)


class ScoreTransfer(BaseModel):
    sender: PlayerName
    receiver: PlayerName
    points: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_different_players(self):
        if self.sender == self.receiver:
            raise ValueError(
                "Sender and receiver must be different"
            )

        return self


class PlayerResponse(BaseModel):
    name: str
    score: int = Field(ge=0)


class RankingResponse(BaseModel):
    ranking: list[PlayerResponse]


class TransferResponse(BaseModel):
    sender: str
    receiver: str
    points: int = Field(gt=0)


class TransferHistoryItem(TransferResponse):
    transfer_id: int = Field(gt=0)
    created_at: datetime | None


class TransferHistoryResponse(BaseModel):
    transfers: list[TransferHistoryItem]


class HealthResponse(BaseModel):
    status: Literal["ok"]


class PlayerDeleteResponse(BaseModel):
    message: str
