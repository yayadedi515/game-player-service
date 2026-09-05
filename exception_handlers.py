from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from player_exceptions import (
    DuplicatePlayerError,
    InsufficientScoreError,
    InvalidTransferError,
    PlayerDeletionRestrictedError,
    PlayerNotFoundError,
    UnexpectedTransferResultError
)
from user_exceptions import DuplicateUserError


BUSINESS_ERROR_RESPONSES = {
    PlayerNotFoundError: (
        404,
        "Player not found"
    ),
    DuplicatePlayerError: (
        400,
        "Invalid or duplicate player"
    ),
    DuplicateUserError: (
        409,
        "Username already exists"
    ),
    PlayerDeletionRestrictedError: (
        409,
        "Player has transfer history"
    ),
    InsufficientScoreError: (
        409,
        "Insufficient score"
    ),
    InvalidTransferError: (
        422,
        "Invalid transfer"
    ),
    UnexpectedTransferResultError: (
        500,
        "Unexpected transfer result"
    ),
}


logger = logging.getLogger(__name__)


async def handle_business_error(
        request: Request,
        error: Exception
):
    status_code, detail = BUSINESS_ERROR_RESPONSES[
        type(error)
    ]

    if status_code >= 500:
        logger.error(
            "Unexpected business error on %s %s: %s",
            request.method,
            request.url.path,
            type(error).__name__,
            exc_info=error
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail
        }
    )


def register_exception_handlers(app: FastAPI):
    for error_type in BUSINESS_ERROR_RESPONSES:
        app.add_exception_handler(
            error_type,
            handle_business_error
        )

    app.add_exception_handler(
        Exception,
        handle_unexpected_exception
    )

async def handle_unexpected_exception(
        request: Request,
        error: Exception
):
    logger.error(
        "Unhandled server error on %s %s: %s",
        request.method,
        request.url.path,
        type(error).__name__,
        exc_info=error
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        }
    )