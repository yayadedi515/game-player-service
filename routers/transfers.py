from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies import get_player_service
from player_exceptions import (
    InsufficientScoreError,
    InvalidTransferError,
    PlayerNotFoundError,
    UnexpectedTransferResultError
)
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
    try:
        transfer_result = service.transfer_score(
            transfer.sender,
            transfer.receiver,
            transfer.points
        )

    except PlayerNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        ) from error

    except InsufficientScoreError as error:
        raise HTTPException(
            status_code=409,
            detail="Insufficient score"
        ) from error

    except InvalidTransferError as error:
        raise HTTPException(
            status_code=422,
            detail="Invalid transfer"
        ) from error

    except UnexpectedTransferResultError as error:
        raise HTTPException(
            status_code=500,
            detail="Unexpected transfer result"
        ) from error

    return transfer_result


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
