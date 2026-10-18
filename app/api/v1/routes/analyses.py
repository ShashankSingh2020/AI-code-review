from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_db
from app.models.analysis import AnalysisJob
from app.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobStatusResponse,
    CompleteAnalysisReportResponse,
    DependencyEdgeResponse,
    FindingResponse,
)
from app.services.orchestrator import PipelineOrchestrator
from app.services.repository_ingestion import RepositoryIngestionService

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.post("", response_model=AnalysisJobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(
    payload: AnalysisJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
) -> AnalysisJobStatusResponse:
    repo_url_str = str(payload.repo_url)
    repo_name = RepositoryIngestionService.extract_repo_name(repo_url_str)

    job = AnalysisJob(
        repo_url=repo_url_str,
        repo_name=repo_name,
        current_stage="QUEUED"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(PipelineOrchestrator.run_pipeline, job.id)
    return AnalysisJobStatusResponse.model_validate(job)


@router.get("/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_analysis_status(
    job_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> AnalysisJobStatusResponse:
    job = await db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found."
        )
    return AnalysisJobStatusResponse.model_validate(job)


@router.get("/{job_id}/findings", response_model=List[FindingResponse])
async def get_analysis_findings(
    job_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> List[FindingResponse]:
    stmt = (
        select(AnalysisJob)
        .options(selectinload(AnalysisJob.findings))
        .where(AnalysisJob.id == job_id)
    )
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found."
        )
    return [FindingResponse.model_validate(f) for f in job.findings]


@router.get("/{job_id}/dependencies", response_model=List[DependencyEdgeResponse])
async def get_analysis_dependencies(
    job_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> List[DependencyEdgeResponse]:
    stmt = (
        select(AnalysisJob)
        .options(selectinload(AnalysisJob.edges))
        .where(AnalysisJob.id == job_id)
    )
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found."
        )
    return [DependencyEdgeResponse.model_validate(e) for e in job.edges]


@router.get("/{job_id}/report", response_model=CompleteAnalysisReportResponse)
async def get_complete_report(
    job_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> CompleteAnalysisReportResponse:
    stmt = (
        select(AnalysisJob)
        .options(
            selectinload(AnalysisJob.findings),
            selectinload(AnalysisJob.edges)
        )
        .where(AnalysisJob.id == job_id)
    )
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found."
        )

    return CompleteAnalysisReportResponse(
        id=job.id,
        repo_url=job.repo_url,
        repo_name=job.repo_name,
        status=job.status,
        current_stage=job.current_stage,
        error_message=job.error_message,
        metrics_summary=job.metrics_summary,
        completed_at=job.completed_at,
        created_at=job.created_at,
        findings=[FindingResponse.model_validate(f) for f in job.findings],
        dependencies=[DependencyEdgeResponse.model_validate(e) for e in job.edges]
    )
