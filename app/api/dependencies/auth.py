
from typing import Annotated, List
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import SecurityScopes
from pydantic import ValidationError
from app.core.configs import get_environment
from app.api.shared_schemas.token import TokenData
from app.api.shared_schemas.oauth2 import oauth2_scheme

_env = get_environment()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=_env.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, _env.SECRET_KEY, algorithm=_env.ALGORITHM)
    return encoded_jwt


def decode_jwt(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)) -> TokenData:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    try:
        payload = jwt.decode(token, _env.SECRET_KEY, algorithms=[_env.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": authenticate_value},
            )

        token_scopes = payload.get("scopes", [])

        token_data = TokenData(scopes=token_scopes, email=email)

        if verify_scopes(scopes_needed=security_scopes, user_scopes=token_data.scopes):
            return token_data
        
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
                headers={"WWW-Authenticate": authenticate_value},
            ) 
    
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )

def verify_scopes(scopes_needed: SecurityScopes, user_scopes: List[str]) -> bool:
    for scope in user_scopes:
        if scope in scopes_needed.scopes:
            return True
    
    return False
