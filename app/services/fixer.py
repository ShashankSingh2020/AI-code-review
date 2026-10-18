from app.core.config import settings

class CodeFixerService:
    def __init__(self):
        self.provider = getattr(settings, "LLM_PROVIDER", "gemini")
        self.api_key = getattr(settings, "GEMINI_API_KEY", None)
        self.model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    async def generate_fix(self, rule_id: str, message: str, file_path: str, line: int, code_context: str = "") -> dict:
        if self.provider == "gemini" and self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)
                prompt = (
                    f"Fix this static code issue in Python:\n"
                    f"Rule: {rule_id}\n"
                    f"Message: {message}\n"
                    f"File: {file_path}:{line}\n"
                    f"Context:\n{code_context}\n\n"
                    f"Provide EXPLANATION: (2 sentences max) then REMEDIATION: (clean python code)"
                )
                res = await model.generate_content_async(prompt)
                raw = res.text
                exp, patch = "Recommended static fix.", raw
                if "REMEDIATION:" in raw:
                    parts = raw.split("REMEDIATION:")
                    exp = parts[0].replace("EXPLANATION:", "").strip()
                    patch = parts[1].strip()
                return {"explanation": exp, "suggested_patch": patch}
            except Exception:
                pass

        # Offline / Mock Fallback
        return {
            "explanation": f"Static analysis rule {rule_id} triggered: {message}.",
            "suggested_patch": (
                f"# Fix for {rule_id} at {file_path}:{line}\n"
                f"try:\n"
                f"    # Replace with specific handling\n"
                f"    pass\n"
                f"except Exception as e:\n"
                f"    logger.error(e)\n"
            )
        }

fixer_service = CodeFixerService()