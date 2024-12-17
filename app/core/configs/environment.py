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
    SENTRY_DSN: str = None

    class Config:
        """Load config file"""

        env_file = ".env"
        extra='ignore'
