from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Route Planner"
    anthropic_api_key: str = ""
    model_name: str = "claude-sonnet-4-20250514"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
