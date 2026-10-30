"""Model adapter foundation. No tools or mutation permissions are registered yet."""

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import get_settings


def build_model() -> OpenAIChatModel:
    settings = get_settings()
    return OpenAIChatModel(
        settings.model_name,
        provider=OpenAIProvider(
            base_url=settings.model_base_url,
            api_key=settings.model_api_key.get_secret_value(),
        ),
    )
