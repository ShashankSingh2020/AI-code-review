SYSTEM_PROMPT = """You are a Principal Software Architect and Security Auditor performing an automated code review.
You will be provided with deterministic static analysis findings, complexity metrics, and dependency relations.
Your task is to synthesize these findings into an executive-level code review summary, highlighting:
1. Architecture & Design Quality
2. Top Security & Robustness Risks
3. Concrete, Actionable Remediation Guidance

Rules:
- Base your review strictly on the provided findings and metrics. Do not fabricate hypothetical vulnerabilities.
- Keep the response structured, clear, and professional.
- Do not output Markdown code fence wrappers (such as ```json) around your final text if unstructured.
"""

def build_review_prompt(repo_name: str, metrics: dict, findings: list) -> str:
    high_sev = [f for f in findings if f.get("severity") in ("CRITICAL", "HIGH")]
    med_sev = [f for f in findings if f.get("severity") == "MEDIUM"]

    findings_summary = f"Total Findings: {len(findings)}\n"
    findings_summary += f"- Critical/High Severity: {len(high_sev)}\n"
    findings_summary += f"- Medium Severity: {len(med_sev)}\n\n"

    findings_summary += "Key Issues Detected:\n"
    for f in (high_sev + med_sev)[:15]:
        findings_summary += f"[{f.get('analyzer')}] {f.get('rule_id')} in {f.get('file_path')}:{f.get('line', '?')} - {f.get('title')}: {f.get('message')}\n"

    return f"""Repository: {repo_name}
Metrics: {metrics}

{findings_summary}

Provide a comprehensive architectural and code health review based on the above evidence.
"""
