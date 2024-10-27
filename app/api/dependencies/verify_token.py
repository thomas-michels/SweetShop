from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, decode
from jwt.exceptions import PyJWKClientError, DecodeError
from app.api.exceptions.authentication_exceptions import (
    UnauthenticatedException,
    UnauthorizedException
)
from app.core.configs import get_environment

_env = get_environment()


async def verify_token(
        scopes: SecurityScopes,
        token: HTTPAuthorizationCredentials
    ) -> dict:

    jwks_client = PyJWKClient(f'https://{_env.AUTH0_DOMAIN}/.well-known/jwks.json')

    if token is None:
        raise UnauthenticatedException()

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(
            token.credentials
        ).key

    except PyJWKClientError as error:
        raise UnauthorizedException(str(error))

    except DecodeError as error:
        raise UnauthorizedException(str(error))

    try:
        payload = decode(
            token.credentials,
            signing_key,
            algorithms=_env.AUTH0_ALGORITHMS,
            audience=_env.AUTH0_API_AUDIENCE,
            issuer=_env.AUTH0_ISSUER,
        )
    except Exception as error:
        raise UnauthorizedException(str(error))

    payload["token"] = token

    return payload
