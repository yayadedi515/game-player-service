from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from dependencies import (
    get_token_service,
    get_user_service
)
from schemas import (
    TokenResponse,
    UserRegister,
    UserResponse
)


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post(
    "/register",
    status_code=201,
    response_model=UserResponse
)
def register_user(
        registration: UserRegister,
        service=Depends(get_user_service)
):
    return service.register_user(
        registration.username,
        registration.password.get_secret_value()
    )


@router.post(
    "/token",
    response_model=TokenResponse
)
def login(
        form_data: Annotated[
            OAuth2PasswordRequestForm,
            Depends()
        ],
        user_service=Depends(get_user_service),
        token_service=Depends(get_token_service)
):
    user = user_service.authenticate_user(
        form_data.username,
        form_data.password
    )

    access_token = (
        token_service.create_access_token(
            user["username"]
        )
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
