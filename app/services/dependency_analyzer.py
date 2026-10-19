import ast
import sys
from pathlib import Path
from typing import List, Dict, Any

class DependencyAnalyzer:
    def __init__(self, target_dir: Path = None):
        self.target_dir = Path(target_dir) if target_dir else None
        # Inbuilt Python Standard Library module names
        self.stdlib_names = getattr(sys, "stdlib_module_names", frozenset([
            "os", "sys", "re", "math", "json", "time", "datetime", "typing",
            "pathlib", "collections", "itertools", "functools", "logging",
            "subprocess", "asyncio", "hashlib", "uuid", "shutil", "unittest"
        ]))

    def _classify_import(self, root_name: str, local_modules: set) -> str:
        if root_name in local_modules:
            return "INTERNAL"
        elif root_name in self.stdlib_names:
            return "STDLIB"
        else:
            return "THIRD_PARTY"

    def extract_dependencies(self, file_path: Path, local_modules: set) -> List[Dict[str, Any]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            module_name = file_path.stem
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root_pkg = alias.name.split(".")[0]
                        category = self._classify_import(root_pkg, local_modules)
                        deps.append({
                            "source_node": module_name,
                            "target_node": alias.name,
                            "category": category,
                            "edge_type": "import",
                            "line_number": node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    root_pkg = mod.split(".")[0] if mod else ""
                    category = self._classify_import(root_pkg, local_modules)
                    for alias in node.names:
                        target = f"{mod}.{alias.name}" if mod else alias.name
                        deps.append({
                            "source_node": module_name,
                            "target_node": target,
                            "category": category,
                            "edge_type": "import_from",
                            "line_number": node.lineno
                        })
        except Exception:
            pass
        return deps

    def analyze(self) -> List[Dict[str, Any]]:
        if not self.target_dir or not self.target_dir.exists():
            return []

        py_files = list(self.target_dir.glob("**/*.py"))
        local_modules = {p.stem for p in py_files}

        all_deps = []
        for py_file in py_files:
            all_deps.extend(self.extract_dependencies(py_file, local_modules))

        # Return unique dependencies capped at 60 for optimal canvas rendering
        seen = set()
        deduped = []
        for dep in all_deps:
            key = (dep["source_node"], dep["target_node"], dep["edge_type"])
            if key not in seen:
                seen.add(key)
                deduped.append(dep)
        return deduped[:60]
