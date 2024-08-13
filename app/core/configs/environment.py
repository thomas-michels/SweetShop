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

    # DATABASE
    DATABASE_HOST: str = "localhost"

    # SECURITY
    SECRET_KEY: str = "test"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    class Config:
        """Load config file"""

        env_file = ".env"
        extra='ignore'
