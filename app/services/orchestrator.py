from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.ai import get_ai_provider
from app.db.session import AsyncSessionLocal
from app.models.analysis import AnalysisJob, JobStatus
from app.models.dependency import DependencyEdge
from app.models.finding import StaticAnalysisFinding
from app.services.dependency_analyzer import DependencyAnalyzer
from app.services.file_classifier import FileClassifierService
from app.services.python_ast_analyzer import PythonASTAnalyzer
from app.services.repository_ingestion import RepositoryIngestionService
from app.services.static_analysis import StaticAnalysisService


class PipelineOrchestrator:
    @classmethod
    async def run_pipeline(cls, job_id: str) -> None:
        async with AsyncSessionLocal() as session:
            job = await session.get(AnalysisJob, job_id)
            if not job:
                return

            repo_path: Path | None = None
            try:
                # Stage 1: Cloning
                job.status = JobStatus.RUNNING
                job.current_stage = "CLONING"
                await session.commit()

                repo_path = await RepositoryIngestionService.clone_repository(job.repo_url, job.id)

                # Stage 2: File Discovery & Classification
                job.current_stage = "INSPECTING_FILES"
                await session.commit()

                classified = FileClassifierService.classify_repository(repo_path)
                py_files = classified["python_files"]
                skipped_files = classified["skipped_files"]

                # Stage 3: Deterministic Static Analysis (Ruff)
                job.current_stage = "STATIC_ANALYSIS"
                await session.commit()

                ruff_findings = await StaticAnalysisService.run_ruff_analysis(repo_path)

                # Stage 4: AST Metrics & Complexity Analysis
                job.current_stage = "AST_ANALYSIS"
                await session.commit()

                ast_findings: list[dict[str, Any]] = []
                complexities: list[float] = []
                func_count = 0
                class_count = 0

                for pf in py_files:
                    f_list, stats = PythonASTAnalyzer.analyze_file(pf, repo_path)
                    ast_findings.extend(f_list)
                    if stats["complexity_avg"] > 0:
                        complexities.append(stats["complexity_avg"])
                    func_count += stats["functions_count"]
                    class_count += stats["classes_count"]

                # Stage 5: Dependency Graph Extraction
                job.current_stage = "DEPENDENCY_ANALYSIS"
                await session.commit()

                edges_data: list[dict[str, Any]] = []
                for pf in py_files:
                    edges = DependencyAnalyzer.extract_dependencies(pf, repo_path)
                    edges_data.extend(edges)

                # Combine & Persist Deterministic Findings
                all_findings_raw = ruff_findings + ast_findings
                for finding in all_findings_raw:
                    session.add(
                        StaticAnalysisFinding(
                            job_id=job.id,
                            file_path=finding["file_path"],
                            line=finding.get("line"),
                            column=finding.get("column"),
                            rule_id=finding["rule_id"],
                            analyzer=finding["analyzer"],
                            severity=finding["severity"],
                            title=finding["title"],
                            message=finding["message"],
                            code_snippet=finding.get("code_snippet")
                        )
                    )

                for edge in edges_data:
                    session.add(
                        DependencyEdge(
                            job_id=job.id,
                            source_node=edge["source_node"],
                            target_node=edge["target_node"],
                            edge_type=edge["edge_type"],
                            line_number=edge.get("line_number")
                        )
                    )

                avg_cc = round(sum(complexities) / len(complexities), 2) if complexities else 1.0
                metrics_summary = {
                    "python_files_count": len(py_files),
                    "skipped_files_count": len(skipped_files),
                    "total_findings_count": len(all_findings_raw),
                    "dependency_edges_count": len(edges_data),
                    "functions_count": func_count,
                    "classes_count": class_count,
                    "avg_complexity": avg_cc
                }

                # Stage 6: AI Synthesis
                job.current_stage = "AI_SYNTHESIS"
                await session.commit()

                ai_provider = get_ai_provider()
                ai_review = await ai_provider.generate_code_review(
                    repo_name=job.repo_name,
                    metrics=metrics_summary,
                    findings=all_findings_raw
                )
                metrics_summary["ai_review"] = ai_review

                # Completion
                job.metrics_summary = metrics_summary
                job.status = JobStatus.COMPLETED
                job.current_stage = "COMPLETED"
                job.completed_at = datetime.now(UTC)
                await session.commit()

            except Exception as exc:
                await session.rollback()
                job = await session.get(AnalysisJob, job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.current_stage = "FAILED"
                    job.error_message = str(exc)
                    await session.commit()
            finally:
                RepositoryIngestionService.cleanup_repository(job_id)
