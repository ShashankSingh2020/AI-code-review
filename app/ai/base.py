from abc import ABC, abstractmethod
from typing import Any


class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_code_review(
        self,
        repo_name: str,
        metrics: dict[str, Any],
        findings: list[dict[str, Any]]
    ) -> str:
        """Generate structured review commentary based on deterministic findings."""
        pass
