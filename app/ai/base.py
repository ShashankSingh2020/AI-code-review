from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_code_review(
        self,
        repo_name: str,
        metrics: Dict[str, Any],
        findings: List[Dict[str, Any]]
    ) -> str:
        """Generate structured review commentary based on deterministic findings."""
        pass
