from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dependencies import get_player_service
from schemas import ScoreTransfer, TransferResponse, TransferHistoryResponse


router = APIRouter(tags=["Transfers"])


@router.post(
    "/transfers",
    status_code=201,
    response_model=TransferResponse
)
def transfer_player_score(
        transfer: ScoreTransfer,
        service=Depends(get_player_service)
):
    return service.transfer_score(
        transfer.sender,
        transfer.receiver,
        transfer.points
    )


@router.get(
    "/transfers",
    response_model=TransferHistoryResponse
)
def get_transfer_history(
        limit: Annotated[
            int,
            Query(ge=1, le=100)
        ] = 20,
        offset: Annotated[
            int,
            Query(ge=0)
        ] = 0,
        service=Depends(get_player_service)
):
    return {
        "transfers": service.get_transfer_history(
            limit=limit,
            offset=offset
        )
    }
