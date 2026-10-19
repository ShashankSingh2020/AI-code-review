import ast
from pathlib import Path

class DependencyAnalyzer:
    def __init__(self, target_dir: Path = None):
        self.target_dir = Path(target_dir) if target_dir else None

    @staticmethod
    def extract_dependencies(file_path: Path) -> list:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            module_name = file_path.stem
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps.append({
                            "source_node": module_name,
                            "target_node": alias.name,
                            "edge_type": "import",
                            "line_number": node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for alias in node.names:
                        target = f"{mod}.{alias.name}" if mod else alias.name
                        deps.append({
                            "source_node": module_name,
                            "target_node": target,
                            "edge_type": "import_from",
                            "line_number": node.lineno
                        })
        except Exception:
            pass
        return deps

    def analyze(self) -> list:
        if not self.target_dir or not self.target_dir.exists():
            return []

        all_deps = []
        for py_file in self.target_dir.glob("**/*.py"):
            all_deps.extend(self.extract_dependencies(py_file))
        return all_deps[:50]  # Cap at 50 to maintain clean graph rendering performance