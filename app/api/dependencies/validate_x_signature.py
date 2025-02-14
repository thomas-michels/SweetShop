import hashlib
import hmac
import urllib.parse
from fastapi import Request

from app.core.configs import get_environment, get_logger

_logger = get_logger(__name__)
_env = get_environment()


def validate_signature(request: Request) -> bool:
    """
    Valida a assinatura HMAC da requisição recebida do Mercado Pago.
    """
    try:
        x_signature = request.headers.get("x-signature")
        x_request_id = request.headers.get("x-request-id")
        query_params = urllib.parse.parse_qs(request.url.query)
        data_id = query_params.get("data.id", [""])[0]

        if not x_signature or not x_request_id or not data_id:
            _logger.error("Missing required headers or query parameters")
            return False

        parts = x_signature.split(",")
        ts, hash_value = None, None

        for part in parts:
            key_value = part.split("=", 1)
            if len(key_value) == 2:
                key, value = key_value[0].strip(), key_value[1].strip()
                if key == "ts":
                    ts = value
                elif key == "v1":
                    hash_value = value

        if not ts or not hash_value:
            _logger.error("Invalid x-signature format")
            return False

        secret = _env.MERCADO_PAGO_WEBHOOK_SECRET
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
        hmac_obj = hmac.new(secret.encode(), msg=manifest.encode(), digestmod=hashlib.sha256)
        sha = hmac_obj.hexdigest()

        if sha == hash_value:
            _logger.info(f"Valid signature {data_id}")
            return True

        _logger.warning(f"Invalid signature {data_id}")
        return False

    except Exception as e:
        _logger.error(f"Error validating signature: {str(e)}")
        return False
