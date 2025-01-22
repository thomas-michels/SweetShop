import resend
from typing import List
from uuid import uuid4
from app.core.configs import get_environment, get_logger

_env = get_environment()
_logger = get_logger(__name__)


def send_email(email_to: List[str], title: str, message: str) -> str:
    try:
        params = {
            "from": _env.DEFAULT_EMAIL,
            "to": email_to,
            "subject": title,
            "html": message,
        }

        if not _env.RESEND_API_KEY and not _env.DEFAULT_EMAIL:
            _logger.info(params)
            return str(uuid4())

        resend.api_key = _env.RESEND_API_KEY

        email_sent = resend.Emails.send(params)

        if email_sent:
            return email_sent["id"]

    except Exception as error:
        _logger.error(f"Some error happen to send email: {str(error)}")
