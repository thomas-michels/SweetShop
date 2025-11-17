import random
import time
import requests
from app.core.configs import get_environment, get_logger

_env = get_environment()
_logger = get_logger(__name__)


class WhatsAppMessageSender:

    def check_whatsapp_numbers(self, number: str) -> bool:
        url = f"{_env.EVOLUTION_BASE_URL}/chat/whatsappNumbers/{_env.EVOLUTION_INSTANCE}"

        headers = {
            "Content-Type": "application/json",
            "apikey": _env.EVOLUTION_API_KEY
        }

        body = {
            "numbers": [number]
        }

        try:
            response = requests.post(
                url=url,
                headers=headers,
                json=body,
                timeout=10
            )

            if response.status_code != 200:
                return False

            return True

        except Exception as e:
            _logger.error(f"Error on check_whatsapp_numbers: {str(e)}")
            return False

    def send_message(self, number: str, message: str) -> dict:
        url = f"{_env.EVOLUTION_BASE_URL}/message/sendText/{_env.EVOLUTION_INSTANCE}"
        headers = {
            "Content-Type": "application/json",
            "apikey": _env.EVOLUTION_API_KEY
        }
        body = {
            "number": number,
            "text": message
        }

        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                delay = random.randint(1, 3)
                time.sleep(delay)

                response = requests.post(
                    url=url,
                    headers=headers,
                    json=body,
                    timeout=10
                )

                if response.status_code == 201:
                    _logger.info(f"Message sent to {number} (attempt {attempt})")
                    return response.json()

                _logger.warning(
                    f"Attempt {attempt}/{max_retries} failed for {number}: "
                    f"status={response.status_code} - {response.text}"
                )

            except Exception as error:
                _logger.error(
                    f"Error on attempt {attempt}/{max_retries} while sending message to {number}: {str(error)}"
                )

            if attempt < max_retries:
                sleep_time = attempt * 2  # 2s, 4s, 6s
                time.sleep(sleep_time)

        _logger.error(
            f"Failed to send message after {max_retries} attempts - number: {number} - message: {message}"
        )
        return None
