"""
Module to load all Environment variables
"""

from pydantic_settings import BaseSettings


class Environment(BaseSettings):
    """
    Environment, add the variable and its type here matching the .env file
    """

    # APPLICATION
    APPLICATION_NAME: str = "Sweet Shop API"
    APPLICATION_HOST: str = "localhost"
    APPLICATION_PORT: int = 8000
    ENVIRONMENT: str = "local"
    RELEASE: str = "0.0.1"

    # DATABASE
    DATABASE_HOST: str = "localhost"

    # SECURITY
    SECRET_KEY: str = "test"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AUTH0
    AUTH0_DOMAIN: str
    AUTH0_API_AUDIENCE: str
    AUTH0_ISSUER: str
    AUTH0_ALGORITHMS: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    APP_SECRET_KEY: str
    AUTH0_MANAGEMENT_API_CLIENT_ID: str
    AUTH0_MANAGEMENT_API_CLIENT_SECRET: str
    AUTH0_MANAGEMENT_API_AUDIENCE: str

    # SENTRY
    SENTRY_DSN: str | None = None

    # RESEND
    DEFAULT_EMAIL: str | None = None
    RESEND_API_KEY: str | None = None

    # TIGRIS
    BUCKET_BASE_URL: str | None = None
    BUCKET_ACCESS_KEY_ID: str | None = None
    BUCKET_SECRET_KEY: str | None = None
    BUCKET_NAME: str | None = None
    BUCKET_URL_EXPIRES_IN_SECONDS: int = 300

    # REDIS
    REDIS_URL: str | None = None
    REDIS_PORT: int | None = None
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None

    # Mercado Pago
    MERCADO_PAGO_ACCESS_TOKEN: str | None = None
    NEXT_PUBLIC_MERCADO_PAGO_PUBLIC_KEY: str | None = None
    MERCADO_PAGO_WEBHOOK_SECRET: str | None = None
    MP_TEST_EMAIL: str | None = None

    # PEDIDOZ
    PEDIDOZ_FRONT_URL: str | None = None


    class Config:
        """Load config file"""

        env_file = ".env"
        extra='ignore'
