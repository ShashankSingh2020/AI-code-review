import ast
import logging

from app.core.config import settings
from app.schemas.fix import FixResponse

logger = logging.getLogger(__name__)

class FixerService:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", None)
        self.model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    @staticmethod
    def verify_python_syntax(code: str) -> bool:
        """Deterministically validates whether generated patch conforms to valid Python AST syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    async def generate_fix(
        self,
        rule_id: str,
        message: str,
        file_path: str,
        line: int,
        code_context: str | None = None
    ) -> FixResponse:
        context_str = code_context.strip() if code_context else f"# Line {line} in {file_path}\n# Rule {rule_id}: {message}"

        # 1. Fallback heuristic patches for common static rules
        fallback_patch = context_str
        fallback_explanation = f"Automated recommendation for {rule_id}: {message}."

        if rule_id == "AST-E001":
            fallback_explanation = "Avoid bare except statements. Catch specific exceptions (e.g. Exception, ValueError) to avoid suppressing system signals."
            fallback_patch = context_str.replace("except:", "except Exception as exc:")
        elif rule_id == "AST-S001":
            fallback_explanation = "Dynamic execution via eval/exec allows arbitrary code injection. Replace with ast.literal_eval or safe dispatch tables."
            fallback_patch = "# REMEDIATION: Replace dynamic execution with safe parser\nimport ast\n# ast.literal_eval(...)"

        # 2. Attempt LLM generation if configured
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)

                prompt = (
                    f"You are an expert static analysis remediation engine.\n"
                    f"Issue: Rule [{rule_id}] - {message}\n"
                    f"Target file: {file_path} (line {line})\n"
                    f"Context snippet:\n```python\n{context_str}\n```\n\n"
                    f"Provide:\n"
                    f"1. A 2-sentence explanation of the vulnerability or style violation.\n"
                    f"2. A minimal, corrected replacement snippet in valid Python syntax.\n"
                    f"Return ONLY valid JSON with keys 'explanation' and 'suggested_patch'."
                )

                response = await model.generate_content_async(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )

                if response and response.text:
                    import json
                    parsed = json.loads(response.text)
                    patch = parsed.get("suggested_patch", fallback_patch)
                    explanation = parsed.get("explanation", fallback_explanation)

                    # Deterministic Verification: check AST syntax validity
                    if self.verify_python_syntax(patch):
                        return FixResponse(
                            rule_id=rule_id,
                            file_path=file_path,
                            line=line,
                            suggested_patch=patch,
                            explanation=explanation
                        )
                    else:
                        logger.warning("LLM patch failed AST syntax verification. Reverting to fallback.")
            except Exception as e:
                logger.error("FixerService LLM execution failed: %s", e)

        return FixResponse(
            rule_id=rule_id,
            file_path=file_path,
            line=line,
            suggested_patch=fallback_patch,
            explanation=fallback_explanation
        )

fixer_service = FixerService()
