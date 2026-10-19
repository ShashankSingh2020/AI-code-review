import ast
from pathlib import Path
from typing import Any, Dict, List, Tuple
from radon.complexity import cc_visit

try:
    from app.models.finding import FindingSeverity
except ImportError:
    class FindingSeverity:
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"


class ASTVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.findings: List[Dict[str, Any]] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            severity = getattr(FindingSeverity, "HIGH", "HIGH")
            self.findings.append({
                "file_path": self.rel_path,
                "line": node.lineno,
                "column": node.col_offset,
                "rule_id": "AST-E001",
                "analyzer": "ast",
                "severity": severity.value if hasattr(severity, "value") else str(severity),
                "title": "Bare Except Clause",
                "message": "Catching generic Exception or bare except hides bugs and interrupts signals.",
                "code_snippet": None
            })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                severity = getattr(FindingSeverity, "CRITICAL", "HIGH")
                self.findings.append({
                    "file_path": self.rel_path,
                    "line": node.lineno,
                    "column": node.col_offset,
                    "rule_id": "AST-S001",
                    "analyzer": "ast",
                    "severity": severity.value if hasattr(severity, "value") else str(severity),
                    "title": f"Dynamic Code Execution ({node.func.id})",
                    "message": f"Use of '{node.func.id}' allows arbitrary code execution.",
                    "code_snippet": None
                })
        self.generic_visit(node)


class PythonASTAnalyzer:
    def __init__(self, target_dir: Path = None):
        self.target_dir = Path(target_dir) if target_dir else None

    @staticmethod
    def analyze_file(file_path: Path, repo_path: Path = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        if repo_path:
            try:
                rel_path = str(file_path.relative_to(repo_path))
            except ValueError:
                rel_path = str(file_path)
        else:
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
                    raw_sev = FindingSeverity.HIGH if block.complexity > 15 else FindingSeverity.MEDIUM
                    sev_str = raw_sev.value if hasattr(raw_sev, "value") else str(raw_sev)
                    findings.append({
                        "file_path": rel_path,
                        "line": block.lineno,
                        "column": block.col_offset,
                        "rule_id": "RADON-CC",
                        "analyzer": "radon",
                        "severity": sev_str,
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

    def analyze(self) -> Dict[str, Any]:
        """Walks target_dir and returns aggregated metrics and findings."""
        if not self.target_dir or not self.target_dir.exists():
            return {
                "file_count": 0,
                "function_count": 0,
                "class_count": 0,
                "complexity_avg": 0.0,
                "findings": []
            }

        py_files = list(self.target_dir.glob("**/*.py"))
        total_functions = 0
        total_classes = 0
        all_complexities = []
        all_findings = []

        for py_file in py_files:
            file_findings, stats = self.analyze_file(py_file, self.target_dir)
            total_functions += stats.get("functions_count", 0)
            total_classes += stats.get("classes_count", 0)
            if stats.get("complexity_avg", 0) > 0:
                all_complexities.append(stats["complexity_avg"])
            all_findings.extend(file_findings)

        overall_avg = sum(all_complexities) / len(all_complexities) if all_complexities else 0.0

        return {
            "file_count": len(py_files),
            "function_count": total_functions,
            "class_count": total_classes,
            "complexity_avg": round(overall_avg, 2),
            "findings": all_findings
        }