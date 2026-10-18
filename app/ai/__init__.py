from app.core.config import settings
from app.ai.base import BaseAIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.gemini_provider import GeminiAIProvider


def get_ai_provider() -> BaseAIProvider:
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        return GeminiAIProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL
        )
    return MockAIProvider()
