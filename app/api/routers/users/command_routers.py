from fastapi import APIRouter, Depends, Security

from app.api.composers import user_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import (
    ConfirmPassword,
    UpdateUser,
    User,
    UserInDB,
    UserServices,
)

router = APIRouter(tags=["Users"])


@router.post("/users", responses={201: {"model": UserInDB}})
async def create_user(
    user: User,
    confirm_password: ConfirmPassword,
    user_services: UserServices = Depends(user_composer),
):
    user_in_db = await user_services.create(
        user=user, confirm_password=confirm_password
    )

    return build_response(
        status_code=201, message="User created with success", data=user_in_db
    )


@router.put("/user/me", responses={200: {"model": UserInDB}})
async def update_user(
    user: UpdateUser,
    current_user: UserInDB = Security(decode_jwt, scopes=["user:me"]),
    user_services: UserServices = Depends(user_composer),
):
    user_in_db = await user_services.update(id=current_user.id, updated_user=user)

    return build_response(
        status_code=200, message="User updated with success", data=user_in_db
    )


@router.put("/user/{user_id}", responses={200: {"model": UserInDB}})
async def update_user(
    user_id: int,
    user: UpdateUser,
    current_user: UserInDB = Security(decode_jwt, scopes=["user:update"]),
    user_services: UserServices = Depends(user_composer),
):
    user_in_db = await user_services.update(id=user_id, updated_user=user)

    return build_response(
        status_code=200, message="User updated with success", data=user_in_db
    )


@router.delete("/user/{user_id}", responses={200: {"model": UserInDB}})
async def delete_user(
    user_id: int,
    current_user: UserInDB = Security(decode_jwt, scopes=["user:delete"]),
    user_services: UserServices = Depends(user_composer),
):
    user_in_db = await user_services.delete_by_id(id=user_id)

    return build_response(
        status_code=200, message="User deleted with success", data=user_in_db
    )


@router.delete("/user/me", responses={200: {"model": UserInDB}})
async def delete_user(
    current_user: UserInDB = Security(decode_jwt, scopes=["user:me"]),
    user_services: UserServices = Depends(user_composer),
):
    user_in_db = await user_services.delete_by_id(id=current_user.id)

    return build_response(
        status_code=200, message="User deleted with success", data=user_in_db
    )
