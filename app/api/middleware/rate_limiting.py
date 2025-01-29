from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.exceptions.authentication_exceptions import TooManyRequestException
from app.core.configs import get_logger
from app.api.dependencies.redis_manager import RedisManager

_logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para limitar a taxa de requisições por IP usando Redis.
    """
    def __init__(self, app: FastAPI, limit: int, window: int):
        super().__init__(app)
        self.redis = RedisManager()
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host

        key = f"rate_limit:{client_ip}"
        request_count = self.redis.increment_value(key, self.window)

        if request_count > self.limit:
            _logger.warning(f"Rate limit exceeded for {client_ip}")
            raise TooManyRequestException()

        response = await call_next(request)
        return response
