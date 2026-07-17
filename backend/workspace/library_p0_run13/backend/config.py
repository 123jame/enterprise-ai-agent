"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Library Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./library.db"
    DATABASE_ECHO: bool = False

    # Borrowing rules
    MAX_BORROW_BOOKS: int = 5
    DEFAULT_BORROW_DAYS: int = 30

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
