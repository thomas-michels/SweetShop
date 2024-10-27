from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from jose import JWTError
from pydantic import ValidationError

from app.api.composers import authentication_composer
from app.api.dependencies.verify_token import verify_token
from app.api.shared_schemas.token import TokenData
from app.core.exceptions.users import NotFoundError
from app.crud.authetication import AuthenticationServices
from app.crud.users.schemas import UserInDB


async def decode_jwt(
    security_scopes: SecurityScopes,
    token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    authetication_services: AuthenticationServices = Depends(authentication_composer),
) -> UserInDB:
    try:
        auth_result = await verify_token(
            scopes=security_scopes,
            token=token
        )

        token_scopes = auth_result.get("scopes", [])

        token_data = TokenData(scopes=token_scopes, id=auth_result["sub"])

        verify_scopes(
            scopes_needed=security_scopes,
            user_scopes=token_data.scopes,
        )

        current_user = await authetication_services.get_current_user(token=token_data)

        if current_user.is_active:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except (JWTError, ValidationError, NotFoundError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_scopes(
    scopes_needed: SecurityScopes, user_scopes: List[str]
) -> bool:
    for scope in user_scopes:
        if scope in scopes_needed.scopes:
            return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied",
        headers={"WWW-Authenticate": "Bearer"},
    )
