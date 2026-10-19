from typing import Any

from google import genai
from google.genai import types

from app.ai.base import BaseAIProvider
from app.ai.prompts import SYSTEM_PROMPT, build_review_prompt


class GeminiAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate_code_review(
        self,
        repo_name: str,
        metrics: dict[str, Any],
        findings: list[dict[str, Any]]
    ) -> str:
        prompt = build_review_prompt(repo_name, metrics, findings)
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
        return response.text if response and response.text else "Review generation returned empty response."
