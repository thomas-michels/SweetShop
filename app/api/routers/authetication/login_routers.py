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


@router.post("/signin", responses={200: {"model": Token}})
async def signin(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    authetication_services: AuthenticationServices = Depends(authentication_composer),
):
    user = UserSignin(email=form_data.username, password=form_data.password)

    user_in_db = await authetication_services.signin(user=user)

    if not user_in_db:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": str(user_in_db.id), "scopes": form_data.scopes},
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/user/me/", responses={200: {"model": UserInDB}})
async def current_user(
    current_user: UserInDB = Security(decode_jwt, scopes=["user:me"]),
):
    return build_response(
        status_code=200, message="User found with success", data=current_user
    )
