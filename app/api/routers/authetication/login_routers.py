from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordRequestForm

from app.api.composers import authentication_composer
from app.api.dependencies import (
    build_response,
    create_access_token,
    decode_jwt,
)
from app.api.shared_schemas.token import Token
from app.crud.authetication import AuthenticationServices, UserSignin
from app.crud.users import UserInDB

router = APIRouter(tags=["Login"])


@router.get("/user/me/", responses={200: {"model": UserInDB}})
async def current_user(
    current_user: UserInDB = Security(decode_jwt, scopes=["user:me"]),
):
    return build_response(
        status_code=200, message="User found with success", data=current_user
    )
