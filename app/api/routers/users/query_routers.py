from typing import List

from fastapi import APIRouter, Depends, Security, Response

from app.api.composers import user_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB, UserServices

router = APIRouter(tags=["Users"])


@router.get("/users/me/", responses={200: {"model": UserInDB}})
async def current_user(
    current_user: UserInDB = Security(decode_jwt, scopes=["user:me"]),
):
    return build_response(
        status_code=200, message="User found with success", data=current_user
    )


@router.get("/users/{user_id}", responses={200: {"model": UserInDB}})
async def get_user_by_id(
    user_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["user:get"]),
    user_services: UserServices = Depends(user_composer),
):
    user_in_db = await user_services.search_by_id(id=user_id)

    if user_in_db:
        return build_response(
            status_code=200, message="User found with success", data=user_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"User {user_id} not found", data=None
        )


@router.get("/users", responses={200: {"model": List[UserInDB]}})
async def get_users(
    current_user: UserInDB = Security(decode_jwt, scopes=["user:get"]),
    user_services: UserServices = Depends(user_composer),
):
    users = await user_services.search_all()

    if users:
        return build_response(
            status_code=200, message="Users found with success", data=users
        )

    else:
        return Response(status_code=204)
