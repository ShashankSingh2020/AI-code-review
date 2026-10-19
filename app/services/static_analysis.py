import json
import subprocess
from pathlib import Path

class StaticAnalysisService:
    @staticmethod
    def run_ruff(target_dir: Path) -> list:
        cmd = [
            "ruff", "check",
            str(target_dir),
            "--select", "E,F,S,B",
            "--output-format", "json",
            "--exit-zero"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if not res.stdout.strip():
                return []
            raw_findings = json.loads(res.stdout)
            findings = []
            for item in raw_findings:
                code = item.get("code", "UNKNOWN")
                severity = "HIGH" if code.startswith("S") else ("MEDIUM" if code.startswith("E") else "LOW")
                filename = item.get("filename", "")
                try:
                    rel_path = str(Path(filename).relative_to(target_dir))
                except Exception:
                    rel_path = filename

                findings.append({
                    "rule_id": code,
                    "severity": severity,
                    "file_path": rel_path,
                    "line": item.get("location", {}).get("row", 1),
                    "title": item.get("message", "Static issue detected"),
                    "message": item.get("message", "")
                })
            return findings
        except Exception as e:
            return [{
                "rule_id": "RUFF_ERR",
                "severity": "LOW",
                "file_path": "linter",
                "line": 1,
                "title": "Linter Execution Error",
                "message": str(e)
            }]

static_analysis_service = StaticAnalysisService()