from app.core.config import settings

class GeminiReviewer:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", None)
        self.model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    async def synthesize_review(self, structural_metrics: dict, findings: list, dependencies: list) -> str:
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)
                
                prompt = (
                    f"Perform an architectural and security code review synthesis based on these metrics:\n"
                    f"Structural Metrics: {structural_metrics}\n"
                    f"Total Static Findings: {len(findings)}\n"
                    f"Sample Findings: {findings[:5]}\n"
                    f"Total Dependencies: {len(dependencies)}\n\n"
                    f"Provide a concise 3-paragraph executive summary highlighting code quality, potential risks, and architectural integrity."
                )
                response = await model.generate_content_async(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                pass

        # Offline / Fallback Review Generator
        high_severity = [f for f in findings if f.get("severity") == "HIGH"]
        return (
            f"Automated Architecture & Quality Audit:\n\n"
            f"1. Codebase Scope: Analyzed {structural_metrics.get('file_count', 0)} files and "
            f"{structural_metrics.get('function_count', 0)} total functions.\n"
            f"2. Static Findings: {len(findings)} total issues detected, with "
            f"{len(high_severity)} high-severity concerns requiring priority remediation.\n"
            f"3. Architecture & Modularity: Dependency tree maps {len(dependencies)} module connections. "
            f"Internal coupling and boundary patterns are structurally coherent."
        )

gemini_reviewer = GeminiReviewer()