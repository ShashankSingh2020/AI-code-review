import ast
from pathlib import Path
from typing import Any, Dict, List, Tuple
from radon.complexity import cc_visit

from app.models.finding import FindingSeverity


class ASTVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.findings: List[Dict[str, Any]] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.findings.append({
                "file_path": self.rel_path,
                "line": node.lineno,
                "column": node.col_offset,
                "rule_id": "AST-E001",
                "analyzer": "ast",
                "severity": FindingSeverity.HIGH,
                "title": "Bare Except Clause",
                "message": "Catching generic Exception or bare except hides bugs and interrupts signals.",
                "code_snippet": None
            })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                self.findings.append({
                    "file_path": self.rel_path,
                    "line": node.lineno,
                    "column": node.col_offset,
                    "rule_id": "AST-S001",
                    "analyzer": "ast",
                    "severity": FindingSeverity.CRITICAL,
                    "title": f"Dynamic Code Execution ({node.func.id})",
                    "message": f"Use of '{node.func.id}' allows arbitrary code execution.",
                    "code_snippet": None
                })
        self.generic_visit(node)


class PythonASTAnalyzer:
    @staticmethod
    def analyze_file(file_path: Path, repo_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        try:
            rel_path = str(file_path.relative_to(repo_path))
        except ValueError:
            rel_path = str(file_path)

        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(code, filename=str(file_path))
        except Exception:
            return findings, {"complexity_avg": 0, "functions_count": 0, "classes_count": 0}

        visitor = ASTVisitor(rel_path)
        visitor.visit(tree)
        findings.extend(visitor.findings)

        # Measure Cyclomatic Complexity via Radon
        try:
            complexity_blocks = cc_visit(code)
            complexities = [b.complexity for b in complexity_blocks]
            avg_complexity = sum(complexities) / len(complexities) if complexities else 0

            for block in complexity_blocks:
                if block.complexity > 10:
                    severity = FindingSeverity.HIGH if block.complexity > 15 else FindingSeverity.MEDIUM
                    findings.append({
                        "file_path": rel_path,
                        "line": block.lineno,
                        "column": block.col_offset,
                        "rule_id": "RADON-CC",
                        "analyzer": "radon",
                        "severity": severity,
                        "title": f"High Cyclomatic Complexity ({block.name})",
                        "message": f"Function/method '{block.name}' has cyclomatic complexity of {block.complexity} (threshold: 10).",
                        "code_snippet": None
                    })
        except Exception:
            avg_complexity = 0
            complexity_blocks = []

        stats = {
            "complexity_avg": round(avg_complexity, 2),
            "functions_count": len([b for b in complexity_blocks if getattr(b, 'letter', '') in ('F', 'M')]),
            "classes_count": len([b for b in complexity_blocks if getattr(b, 'letter', '') == 'C'])
        }

        return findings, stats
