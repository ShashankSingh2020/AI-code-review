from typing import Any, Dict, List
from app.ai.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    async def generate_code_review(
        self,
        repo_name: str,
        metrics: Dict[str, Any],
        findings: List[Dict[str, Any]]
    ) -> str:
        total = len(findings)
        critical_high = [f for f in findings if f.get("severity") in ("CRITICAL", "HIGH")]

        summary = [
            f"## Automated Code Health Summary for `{repo_name}`",
            "",
            f"- **Analyzed Files**: {metrics.get('python_files_count', 0)} Python source files",
            f"- **Average Cyclomatic Complexity**: {metrics.get('avg_complexity', 0.0)}",
            f"- **Total Identified Issues**: {total} (High/Critical: {len(critical_high)})",
            "",
            "### Architectural Assessment",
            "The repository's modules were scanned for structural complexity, circular patterns, and runtime hazards.",
        ]

        if critical_high:
            summary.append("\n### High Priority Remediations")
            for f in critical_high[:5]:
                summary.append(f"- **{f.get('file_path')}:{f.get('line', 1)}**: {f.get('title')} ({f.get('rule_id')})")
        else:
            summary.append("\n### Risk Assessment")
            summary.append("No critical security or runtime hazards were detected by static heuristics.")

        summary.append("\n### Suggested Next Steps")
        summary.append("1. Resolve flagged style and error warnings using standard auto-formatters (e.g., `ruff check --fix`).")
        summary.append("2. Refactor complex functions exceeding cyclomatic complexity thresholds.")

        return "\n".join(summary)
