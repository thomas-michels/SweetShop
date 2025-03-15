
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from jose import JWTError
from pydantic import ValidationError

from app.api.composers import authentication_composer
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.dependencies.verify_token import verify_token
from app.api.shared_schemas.token import TokenData
from app.core.exceptions.users import NotFoundError
from app.core.utils.permissions import get_role_permissions
from app.crud.authetication import AuthenticationServices
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.users.schemas import CompleteUserInDB


async def decode_jwt(
    security_scopes: SecurityScopes,
    token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    organization_id: str = Depends(check_current_organization),
    authetication_services: AuthenticationServices = Depends(authentication_composer),
) -> CompleteUserInDB:
    try:
        auth_result = await verify_token(
            scopes=security_scopes,
            token=token
        )

        token_scopes = auth_result.get("scopes", [])

        token_data = TokenData(scopes=token_scopes, id=auth_result["sub"])

        current_user = await authetication_services.get_current_user(
            token=token_data,
            expand=["organizations"]
        )

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not organization_id:
            return current_user

        if organization_id not in current_user.organizations_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this organization!",
                headers={"WWW-Authenticate": "Bearer"},
            )

        verify_scopes(
            scopes_needed=security_scopes,
            user_role=current_user.organizations_roles[organization_id].role,
            current_user=current_user
        )

        return current_user

    except (JWTError, ValidationError, NotFoundError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_scopes(
    scopes_needed: SecurityScopes | list, user_role: RoleEnum, current_user: CompleteUserInDB
) -> bool:
    user_scopes = get_role_permissions(role=user_role)

    scopes = []

    if isinstance(scopes_needed, SecurityScopes):
        scopes = scopes_needed.scopes

    else:
        scopes = scopes_needed

    if not scopes:
        return True

    for scope in scopes:
        if scope in user_scopes:
            return True

        # Only super users can use that
        if scope in ["user:get"]:
            if current_user.app_metadata and current_user.app_metadata.get("superuser", False):
                return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_super_user(current_user: CompleteUserInDB):
    # if current_user.app_metadata and current_user.app_metadata.get("superuser", False):
    if current_user.app_metadata:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied",
        headers={"WWW-Authenticate": "Bearer"},
    )
