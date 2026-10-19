import time
import asyncio
from pathlib import Path
from app.services.repository_ingestion import repo_ingestion_service
from app.services.python_ast_analyzer import PythonASTAnalyzer
from app.services.static_analysis import static_analysis_service
from app.services.dependency_analyzer import DependencyAnalyzer
from app.services.fixer import fixer_service

BENCHMARK_REPO = "https://github.com/pallets/click.git"
BENCHMARK_BRANCH = "main"

SYNTHETIC_FINDINGS_SET = [
    {"rule_id": "AST-E001", "msg": "Bare except clause", "context": "try:\n    val = 1 / 0\nexcept:\n    pass"},
    {"rule_id": "AST-S001", "msg": "Dynamic execution", "context": "def run(x):\n    eval(x)"},
    {"rule_id": "E722", "msg": "Do not use bare except", "context": "try:\n    data = load()\nexcept:\n    data = None"},
    {"rule_id": "B007", "msg": "Unused loop variable", "context": "for i in range(10):\n    print('tick')"},
    {"rule_id": "S102", "msg": "Use of exec", "context": "exec('print(1)')"}
]

async def run_benchmark():
    print("=" * 60)
    print("1. RUNNING PIPELINE THROUGHPUT BENCHMARK (pallets/click)")
    print("=" * 60)

    # Ingestion benchmark
    t0 = time.perf_counter()
    cloned_path = repo_ingestion_service.clone_repository(BENCHMARK_REPO, BENCHMARK_BRANCH)
    t_clone = time.perf_counter() - t0
    print(f"Clone & Ingestion Time   : {t_clone:.2f}s")

    try:
        # Static & AST Engine benchmark
        t1 = time.perf_counter()
        
        # AST & Radon
        t_ast_start = time.perf_counter()
        ast_analyzer = PythonASTAnalyzer(cloned_path)
        ast_results = ast_analyzer.analyze()
        t_ast = time.perf_counter() - t_ast_start
        
        # Ruff
        t_ruff_start = time.perf_counter()
        ruff_findings = static_analysis_service.run_ruff(cloned_path)
        t_ruff = time.perf_counter() - t_ruff_start

        # Dependency Analyzer
        t_dep_start = time.perf_counter()
        dep_analyzer = DependencyAnalyzer(cloned_path)
        deps = dep_analyzer.analyze()
        t_dep = time.perf_counter() - t_dep_start

        total_analysis_time = time.perf_counter() - t1
        file_count = ast_results.get("file_count", 0)
        func_count = ast_results.get("function_count", 0)
        total_findings = len(ruff_findings) + len(ast_results.get("findings", []))
        throughput = file_count / total_analysis_time if total_analysis_time > 0 else 0

        print(f"Total Files Scanned      : {file_count}")
        print(f"Total Functions Parsed   : {func_count}")
        print(f"Total Findings Detected  : {total_findings}")
        print(f"AST & Radon Time         : {t_ast:.2f}s")
        print(f"Ruff Lint & Security Time: {t_ruff:.2f}s")
        print(f"Dependency Graph Time    : {t_dep:.2f}s")
        print(f"Total Pure Analysis Time : {total_analysis_time:.2f}s")
        print(f"Engine Throughput Rate   : {throughput:.1f} files/sec")
    finally:
        repo_ingestion_service.cleanup(cloned_path)

    print("\n" + "=" * 60)
    print("2. RUNNING AI DETERMINISTIC AST VERIFICATION EVALUATION")
    print("=" * 60)

    valid_patches = 0
    total_evals = len(SYNTHETIC_FINDINGS_SET)

    for idx, item in enumerate(SYNTHETIC_FINDINGS_SET, 1):
        resp = await fixer_service.generate_fix(
            rule_id=item["rule_id"],
            message=item["msg"],
            file_path="sample.py",
            line=1,
            code_context=item["context"]
        )
        is_valid = fixer_service.verify_python_syntax(resp.suggested_patch)
        if is_valid:
            valid_patches += 1
        print(f"Test {idx}/{total_evals} [{item['rule_id']}]: {'PASSED (Valid AST)' if is_valid else 'FAILED'}")

    pass_rate = (valid_patches / total_evals) * 100
    print(f"\nTotal Patches Evaluated  : {total_evals}")
    print(f"Syntactically Valid Patches: {valid_patches}")
    print(f"Deterministic Pass Rate  : {pass_rate:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
