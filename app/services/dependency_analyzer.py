import ast
from pathlib import Path
from typing import Any, Dict, List


class DependencyVisitor(ast.NodeVisitor):
    def __init__(self, source_module: str):
        self.source_module = source_module
        self.edges: List[Dict[str, Any]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.edges.append({
                "source_node": self.source_module,
                "target_node": alias.name,
                "edge_type": "IMPORT",
                "line_number": node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        target = node.module if node.module else "."
        for alias in node.names:
            full_target = f"{target}.{alias.name}" if target != "." else alias.name
            self.edges.append({
                "source_node": self.source_module,
                "target_node": full_target,
                "edge_type": "IMPORT_FROM",
                "line_number": node.lineno
            })
        self.generic_visit(node)


class DependencyAnalyzer:
    @staticmethod
    def extract_dependencies(file_path: Path, repo_path: Path) -> List[Dict[str, Any]]:
        try:
            rel_path = file_path.relative_to(repo_path)
            module_name = str(rel_path.with_suffix("")).replace("\\", ".").replace("/", ".")
        except ValueError:
            module_name = file_path.stem

        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(code, filename=str(file_path))
        except Exception:
            return []

        visitor = DependencyVisitor(module_name)
        visitor.visit(tree)
        return visitor.edges
