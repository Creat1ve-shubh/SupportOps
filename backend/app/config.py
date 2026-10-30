from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://supportops:supportops_local@127.0.0.1:5432/supportops"
    model_base_url: str = "http://localhost:11434/v1"
    model_name: str = "qwen3:8b"
    model_api_key: SecretStr = SecretStr("ollama")
    agent_max_tool_calls: int = Field(default=12, ge=1, le=100)
    agent_timeout_seconds: int = Field(default=60, ge=1, le=600)

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Hosted providers such as Neon hand out plain postgresql:// URLs.
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
