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
            response = requests.post(url, headers=headers, json=body)

            if response.status_code != 200:
                return False

            return True

        except Exception as e:
            _logger.error(f"Error on check_whatsapp_numbers: {str(e)}")
            return False

    def send_message(self, number: str, message: str) -> dict:
        delay = random.randint(1, 3)
        time.sleep(delay)

        url = f"{_env.EVOLUTION_BASE_URL}/message/sendText/{_env.EVOLUTION_INSTANCE}"
        headers = {
            "Content-Type": "application/json",
            "apikey": _env.EVOLUTION_API_KEY
        }
        body = {
            "number": number,
            "text": message
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code != 201:
            raise Exception(f"Falha ao enviar mensagem para {number}: {response.text}")

        _logger.info(f"Message sent to {number}")
        return response.json()
