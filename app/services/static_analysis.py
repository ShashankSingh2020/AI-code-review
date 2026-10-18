import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from app.models.finding import FindingSeverity


def _map_ruff_code_to_severity(code: str) -> FindingSeverity:
    if code.startswith("S"):
        return FindingSeverity.HIGH
    if code.startswith("F"):
        return FindingSeverity.HIGH
    if code.startswith("E") or code.startswith("W"):
        return FindingSeverity.MEDIUM
    if code.startswith("B"):
        return FindingSeverity.MEDIUM
    if code.startswith("C90"):
        return FindingSeverity.MEDIUM
    return FindingSeverity.LOW


def _sync_run_ruff(repo_path: Path) -> str:
    cmd = [
        "ruff",
        "check",
        str(repo_path),
        "--output-format=json",
        "--exit-zero"
    ]
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return res.stdout.strip()


class StaticAnalysisService:
    @staticmethod
    async def run_ruff_analysis(repo_path: Path) -> List[Dict[str, Any]]:
        raw_output = await asyncio.to_thread(_sync_run_ruff, repo_path)
        if not raw_output:
            return []

        try:
            raw_findings = json.loads(raw_output)
        except json.JSONDecodeError:
            return []

        normalized_findings: List[Dict[str, Any]] = []
        for item in raw_findings:
            file_abs_path = Path(item.get("filename", ""))
            try:
                rel_path = str(file_abs_path.relative_to(repo_path))
            except ValueError:
                rel_path = str(file_abs_path)

            code = item.get("code", "RUFF")
            message = item.get("message", "Lint warning")
            location = item.get("location", {})

            normalized_findings.append({
                "file_path": rel_path,
                "line": location.get("row", 1),
                "column": location.get("column", 1),
                "rule_id": code,
                "analyzer": "ruff",
                "severity": _map_ruff_code_to_severity(code),
                "title": f"Ruff: {code}",
                "message": message,
                "code_snippet": None
            })

        return normalized_findings
