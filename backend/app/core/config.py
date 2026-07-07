from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str

    APP_VERSION: str

    DEBUG: bool

    HOST: str

    PORT: int

    OPENAI_API_KEY: str

    OPENAI_BASE_URL: str

    MODEL_NAME: str

    TEMPERATURE: float

    MAX_TOKENS: int

    LOG_LEVEL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


@lru_cache
def get_settings():

    return Settings()


settings = get_settings()