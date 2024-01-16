from typing import Annotated
from fastapi import APIRouter, Depends, Security, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.api.dependencies import build_response, create_access_token, decode_jwt
from app.api.composers import authentication_composer
from app.api.shared_schemas.token import Token, TokenData
from app.crud.authetication import AuthenticationServices, UserSignin
from app.crud.users import UserInDB


router = APIRouter(tags=["Login"])


@router.post("/signin", responses={200: {"model": Token}})
async def signin(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    authetication_services: AuthenticationServices = Depends(authentication_composer)
):
    user = UserSignin(email=form_data.username, password=form_data.password)

    user_in_db = await authetication_services.signin(user=user)

    if not user_in_db:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": user_in_db.email, "scopes": form_data.scopes},
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/user/me/", responses={200: {"model": UserInDB}})
async def current_user(
    token: TokenData = Security(decode_jwt, scopes=["me"]),
    authetication_services: AuthenticationServices = Depends(authentication_composer)
):
    user_in_db = await authetication_services.get_current_user(token=token)

    return build_response(
        status_code=200,
        message="User found with success",
        data=user_in_db
    )
