from app.core.utils.http_client import HTTPClient
from app.core.configs import get_environment, get_logger

_env = get_environment()
_logger = get_logger(__name__)


def get_address_by_zip_code(zip_code: str) -> dict:
    _logger.info(f"Getting address by zip code {zip_code}")
    zip_code = ''.join(filter(str.isdigit, zip_code))

    http_client = HTTPClient(headers={})

    url = f"{_env.VIACEP_LINK}/ws/{zip_code}/json/"
    status_code, data = http_client.get(url)

    if status_code == 200:
        if "erro" not in data:
            _logger.info(f"Zip code {zip_code} found with success")
            return data

    _logger.warning(f"Zip code {zip_code} NOT found")
    return None
