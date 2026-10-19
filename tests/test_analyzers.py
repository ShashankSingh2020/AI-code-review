# tests/test_analyzers.py
import pytest
from pathlib import Path
from app.services.python_ast_analyzer import PythonASTAnalyzer
from app.services.dependency_analyzer import DependencyAnalyzer

@pytest.fixture
def sample_python_repo(tmp_path: Path):
    """Creates a temporary mock repository with known issues and imports."""
    file_a = tmp_path / "module_a.py"
    file_a.write_text(
        "import os\n"
        "from typing import Optional\n\n"
        "def risky_fn():\n"
        "    try:\n"
        "        x = 1 / 0\n"
        "    except:\n"  # Bare except -> AST-E001
        "        pass\n\n"
        "def execute_dynamic(code_str):\n"
        "    eval(code_str)\n"  # Dynamic execution -> AST-S001
    )

    file_b = tmp_path / "module_b.py"
    file_b.write_text(
        "import module_a\n\n"
        "class Worker:\n"
        "    def run(self, val):\n"
        "        # Increase complexity\n"
        "        if val == 1: return 'a'\n"
        "        elif val == 2: return 'b'\n"
        "        elif val == 3: return 'c'\n"
        "        elif val == 4: return 'd'\n"
        "        elif val == 5: return 'e'\n"
        "        elif val == 6: return 'f'\n"
        "        elif val == 7: return 'g'\n"
        "        elif val == 8: return 'h'\n"
        "        elif val == 9: return 'i'\n"
        "        elif val == 10: return 'j'\n"
        "        elif val == 11: return 'k'\n"
        "        return 'default'\n"
    )
    return tmp_path

def test_ast_analyzer_detects_security_and_syntax(sample_python_repo):
    analyzer = PythonASTAnalyzer(sample_python_repo)
    results = analyzer.analyze()

    assert results["file_count"] == 2
    assert results["function_count"] >= 3
    assert results["class_count"] == 1

    rule_ids = [f["rule_id"] for f in results["findings"]]
    assert "AST-E001" in rule_ids, "Failed to flag bare except handler"
    assert "AST-S001" in rule_ids, "Failed to flag eval() execution"
    assert "RADON-CC" in rule_ids, "Failed to flag cyclomatic complexity threshold"

def test_dependency_analyzer_extracts_edges(sample_python_repo):
    dep_analyzer = DependencyAnalyzer(sample_python_repo)
    deps = dep_analyzer.analyze()

    targets = [d["target_node"] for d in deps]
    assert "os" in targets
    assert "typing.Optional" in targets
    assert "module_a" in targets