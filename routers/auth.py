from fastapi import APIRouter, Depends

from dependencies import get_user_service
from schemas import UserRegister, UserResponse


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
