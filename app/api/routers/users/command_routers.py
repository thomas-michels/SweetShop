from fastapi import APIRouter, Depends, Security
from app.api.dependencies import build_response
from app.api.composers import user_composer
from app.crud.users import User, UpdateUser, UserInDB, UserServices, ConfirmPassword


router = APIRouter(tags=["Users"])


@router.post("/users", responses={201: {"model": UserInDB}})
async def create_user(
    user: User,
    confirm_password: ConfirmPassword,
    user_services: UserServices = Depends(user_composer)
):
    user_in_db = await user_services.create(user=user, confirm_password=confirm_password)

    return build_response(
        status_code=201,
        message="User created with success",
        data=user_in_db
    )


@router.put("/user/{user_id}", responses={200: {"model": UserInDB}})
async def update_user(user_id: int, user: UpdateUser, user_services: UserServices = Depends(user_composer)):
    user_in_db = await user_services.update(id=user_id, updated_user=user)

    return build_response(
        status_code=200,
        message="User updated with success",
        data=user_in_db
    )


@router.delete("/user/{user_id}", responses={200: {"model": UserInDB}})
async def delete_user(user_id: int, user_services: UserServices = Depends(user_composer)):
    user_in_db = await user_services.delete_by_id(id=user_id)

    return build_response(
        status_code=200,
        message="User deleted with success",
        data=user_in_db
    )
