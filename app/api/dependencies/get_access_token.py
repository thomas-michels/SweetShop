from datetime import datetime, timedelta
from fastapi import Request
from app.core.configs import get_environment, get_logger
from app.core.exceptions.internal import InternalErrorException
from app.core.utils.http_client import HTTPClient

_env = get_environment()
logger = get_logger(__name__)


async def get_access_token(request: Request) -> str:
    logger.info("Getting access token")

    stored_access_token = request.app.state.access_token

    if stored_access_token and datetime.now() < stored_access_token["expires_at"]:
        logger.info("Getting cached access token")
        token = stored_access_token["access_token"]

    else:
        logger.info("Generating new access token")
        access_token = generate_new_access_token()

        expires_at = datetime.now() + timedelta(seconds=access_token.get("expires_in", 0))

        access_token["expires_at"] = expires_at

        request.app.state.access_token = access_token

        token = access_token['access_token']

    if token:
        return f"Bearer {token}"

    logger.error(f"Failed to get an access token. stored_access_token: {stored_access_token}")
    raise InternalErrorException(detail="Internal authentication error!")


def generate_new_access_token() -> dict:
    headers = {
        'content-type':
        "application/x-www-form-urlencoded"
    }

    payload = {
        "grant_type": "client_credentials",
        "client_id": _env.AUTH0_MANAGEMENT_API_CLIENT_ID,
        "client_secret": _env.AUTH0_MANAGEMENT_API_CLIENT_SECRET,
        "audience": _env.AUTH0_MANAGEMENT_API_AUDIENCE
    }

    http_client = HTTPClient(headers=headers)

    status_code, response = http_client.post(
        url=f"{_env.AUTH0_DOMAIN}/oauth/token",
        data=payload
    )

    match status_code:
        case 200:
            return response

        case _:
            logger.error("Failed to generate an access token in Auth0")
            logger.error(f"payload: {payload}")
            logger.error(f"url: {_env.AUTH0_DOMAIN}/oauth/token")
            logger.error(f"status_code: {status_code} - response: {response}")
            raise InternalErrorException(detail="Internal authentication error!")
