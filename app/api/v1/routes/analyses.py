import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import gemini_reviewer
from app.db.session import async_session_factory, get_async_db
from app.models.analysis import AnalysisJob, JobStatus
from app.schemas.fix import FixRequest, FixResponse
from app.services.dependency_analyzer import DependencyAnalyzer
from app.services.fixer import fixer_service
from app.services.python_ast_analyzer import PythonASTAnalyzer
from app.services.repository_ingestion import repo_ingestion_service
from app.services.static_analysis import static_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyses", tags=["analyses"])


async def run_analysis_pipeline(job_id: str, repo_url: str, branch_name: str, repo_name: str):
    """Background worker task running completely outside the HTTP request-response cycle."""
    cloned_path = None
    async with async_session_factory() as db:
        try:
            # 1. Update status to RUNNING
            query = select(AnalysisJob).where(AnalysisJob.id == job_id)
            res = await db.execute(query)
            job = res.scalar_one_or_none()
            if job:
                job.status = JobStatus.RUNNING
                job.current_stage = "CLONING_REPOSITORY"
                await db.commit()

            # 2. Clone repository
            cloned_path = repo_ingestion_service.clone_repository(repo_url, branch_name)

            if job:
                job.current_stage = "STATIC_AND_AST_ANALYSIS"
                await db.commit()

            # 3. AST and Radon Structural Analysis
            ast_analyzer = PythonASTAnalyzer(cloned_path)
            ast_results = ast_analyzer.analyze()
            ast_findings = ast_results.pop("findings", [])

            structural_metrics = {
                "file_count": ast_results.get("file_count", 0),
                "function_count": ast_results.get("function_count", 0),
                "class_count": ast_results.get("class_count", 0),
                "complexity_avg": ast_results.get("complexity_avg", 0.0)
            }

            # 4. Ruff Linter Analysis
            ruff_findings = static_analysis_service.run_ruff(cloned_path)
            all_findings = ast_findings + ruff_findings

            # 5. Dependency Analysis
            dep_analyzer = DependencyAnalyzer(cloned_path)
            dependencies = dep_analyzer.analyze()

            # 6. Gemini Synthesis
            ai_summary = "Automated static and structural code audit completed."
            try:
                ai_summary = await gemini_reviewer.synthesize_review(
                    structural_metrics=structural_metrics,
                    findings=all_findings,
                    dependencies=dependencies
                )
            except Exception as ai_err:
                logger.warning("Gemini synthesis fallback invoked: %s", ai_err)

            # 7. Update Job Status to COMPLETED
            res = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
            job = res.scalar_one_or_none()
            if job:
                job.status = JobStatus.COMPLETED
                job.current_stage = "COMPLETED"
                job.metrics_summary = structural_metrics
                job.raw_structural_metrics = structural_metrics
                job.raw_findings = all_findings
                job.raw_dependencies = dependencies
                job.ai_summary = ai_summary
                job.completed_at = datetime.now(UTC)
                await db.commit()

        except Exception as exc:
            logger.error("Background analysis job %s failed: %s", job_id, exc)
            try:
                res = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
                job = res.scalar_one_or_none()
                if job:
                    job.status = JobStatus.FAILED
                    job.current_stage = "FAILED"
                    job.error_message = str(exc)
                    await db.commit()
            except Exception as rollback_err:
                logger.error("Failed to persist job failure status: %s", rollback_err)
        finally:
            if cloned_path:
                repo_ingestion_service.cleanup(cloned_path)


@router.get("", response_model=dict)
async def get_scan_history(db: AsyncSession = Depends(get_async_db)):
    try:
        query = select(AnalysisJob).order_by(AnalysisJob.created_at.desc()).limit(20)
        res = await db.execute(query)
        jobs = res.scalars().all()
        history = [
            {
                "job_id": j.id,
                "repo_url": j.repo_url,
                "branch_name": j.branch_name,
                "status": j.status.value if hasattr(j.status, "value") else str(j.status),
                "total_files": (j.raw_structural_metrics or {}).get("file_count", 0),
                "total_findings": len(j.raw_findings or []),
                "created_at": j.created_at.isoformat() if j.created_at else None
            }
            for j in jobs
        ]
        return {"history": history}
    except Exception as exc:
        logger.error("Failed to query scan history: %s", exc)
        return {"history": []}


@router.get("/{job_id}", response_model=dict)
async def get_scan_by_id(job_id: str, db: AsyncSession = Depends(get_async_db)):
    query = select(AnalysisJob).where(AnalysisJob.id == job_id)
    res = await db.execute(query)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")

    return {
        "job_id": job.id,
        "repo_url": job.repo_url,
        "branch_name": job.branch_name,
        "status": job.status.value if hasattr(job.status, "value") else str(job.status),
        "current_stage": job.current_stage,
        "error_message": job.error_message,
        "structural_metrics": job.raw_structural_metrics or {},
        "findings": job.raw_findings or [],
        "dependencies": job.raw_dependencies or [],
        "ai_summary": job.ai_summary or "",
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


@router.post("", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    repo_url = payload.get("repo_url", "").strip()
    branch_name = payload.get("branch_name", "main").strip() or "main"

    if not repo_ingestion_service.validate_url(repo_url):
        raise HTTPException(status_code=400, detail="Invalid repository URL. Must be an HTTPS GitHub URL.")

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "") or "repository"

    # Persist pending job state immediately
    new_job = AnalysisJob(
        id=job_id,
        repo_url=repo_url,
        repo_name=repo_name,
        branch_name=branch_name,
        status=JobStatus.PENDING,
        current_stage="QUEUED",
        metrics_summary={},
        raw_structural_metrics={},
        raw_findings=[],
        raw_dependencies=[],
        ai_summary="",
        created_at=datetime.now(UTC)
    )
    db.add(new_job)
    await db.commit()

    # Hand off execution to background queue
    background_tasks.add_task(
        run_analysis_pipeline,
        job_id=job_id,
        repo_url=repo_url,
        branch_name=branch_name,
        repo_name=repo_name
    )

    return {
        "job_id": job_id,
        "repo_url": repo_url,
        "branch_name": branch_name,
        "status": "PENDING",
        "message": "Scan job queued successfully."
    }


@router.post("/fix", response_model=FixResponse)
async def fix_finding(payload: FixRequest):
    try:
        return await fixer_service.generate_fix(
            payload.rule_id,
            payload.message,
            payload.file_path,
            payload.line,
            payload.code_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
