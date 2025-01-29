import redis
from app.core.configs import get_environment, get_logger

_env = get_environment()
_logger = get_logger(__name__)


class RedisManager:
    """
    Classe para gerenciamento de conexões e operações com o Redis.
    """

    def __init__(self):
        self.client = redis.Redis(
            host=_env.REDIS_URL,
            port=_env.REDIS_PORT,
            username=_env.REDIS_USERNAME,
            password=_env.REDIS_PASSWORD,
            decode_responses=True,
        )

    def set_value(self, key: str, value: str, expiration: int = None) -> bool:
        """
        Define um valor no Redis.

        :param key: Chave do valor.
        :param value: Valor a ser armazenado.
        :param expiration: Tempo de expiração em segundos (opcional).
        :return: True se bem-sucedido, False caso contrário.
        """
        try:
            _logger.info(f"Setting key '{key}' in Redis...")
            self.client.set(key, value, ex=expiration)
            return True
        except Exception as error:
            _logger.error(f"Error setting key '{key}': {error}")
            return False

    def get_value(self, key: str) -> str:
        """
        Obtém um valor do Redis.

        :param key: Chave do valor.
        :return: Valor armazenado ou None se não encontrado.
        """
        try:
            _logger.info(f"Getting key '{key}' from Redis...")
            return self.client.get(key)
        except Exception as error:
            _logger.error(f"Error getting key '{key}': {error}")
            return None

    def delete_value(self, key: str) -> bool:
        """
        Deleta um valor do Redis.

        :param key: Chave do valor.
        :return: True se a chave foi deletada, False caso contrário.
        """
        try:
            _logger.info(f"Deleting key '{key}' from Redis...")
            return self.client.delete(key) > 0
        except Exception as error:
            _logger.error(f"Error deleting key '{key}': {error}")
            return False

    def list_keys(self, pattern: str = "*") -> list:
        """
        Lista as chaves armazenadas no Redis com base em um padrão.

        :param pattern: Padrão opcional para filtragem.
        :return: Lista de chaves encontradas.
        """
        try:
            _logger.info(f"Listing keys with pattern '{pattern}'...")
            return self.client.keys(pattern)
        except Exception as error:
            _logger.error(f"Error listing keys: {error}")
            return []

    def increment_value(self, key: str, expiration: int) -> int:
        """
        Incrementa um valor no Redis e define um tempo de expiração se necessário.
        """
        try:
            _logger.info(f"Incrementing key '{key}' in Redis...")
            value = self.client.incr(key)
            if value == 1:
                self.client.expire(key, expiration)
            return value
        except Exception as error:
            _logger.error(f"Error incrementing key '{key}': {error}")
            return 0
