from typing import List

from fastapi import APIRouter, Depends, Security

from app.api.composers import user_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB, UserServices

router = APIRouter(tags=["Users"])


@router.get("/user/{user_id}", responses={200: {"model": UserInDB}})
async def get_user_by_id(
    user_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["user:get"]),
    user_services: UserServices = Depends(user_composer),
):
    user_in_db = await user_services.search_by_id(id=user_id)

    return build_response(
        status_code=200, message="User found with success", data=user_in_db
    )


@router.get("/users", responses={200: {"model": List[UserInDB]}})
async def get_users(
    current_user: UserInDB = Security(decode_jwt, scopes=["user:get"]),
    user_services: UserServices = Depends(user_composer),
):
    users = await user_services.search_all()

    return build_response(
        status_code=200, message="Users found with success", data=users
    )
