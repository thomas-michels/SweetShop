from fastapi import APIRouter, Security
from app.api.dependencies import (
    build_response,
    decode_jwt,
)
from app.crud.users import UserInDB

router = APIRouter(tags=["Login"])


@router.get("/user/me/", responses={200: {"model": UserInDB}})
async def current_user(
    current_user: UserInDB = Security(decode_jwt, scopes=["user:me"]),
):
    return build_response(
        status_code=200, message="User found with success", data=current_user
    )
