from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from app.models.analysis import JobStatus
from app.models.finding import FindingSeverity


class AnalysisJobCreate(BaseModel):
    repo_url: HttpUrl = Field(
        ...,
        description="Public GitHub repository URL (e.g., https://github.com/psf/requests)",
        examples=["https://github.com/octocat/Hello-World"]
    )


class FindingResponse(BaseModel):
    id: str
    file_path: str
    line: int | None = None
    column: int | None = None
    rule_id: str
    analyzer: str
    severity: FindingSeverity
    title: str
    message: str
    code_snippet: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class DependencyEdgeResponse(BaseModel):
    id: str
    source_node: str
    target_node: str
    edge_type: str
    line_number: int | None = None

    class Config:
        from_attributes = True


class AnalysisJobStatusResponse(BaseModel):
    id: str
    repo_url: str
    repo_name: str
    status: JobStatus
    current_stage: str
    error_message: str | None = None
    metrics_summary: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompleteAnalysisReportResponse(AnalysisJobStatusResponse):
    findings: list[FindingResponse] = Field(default_factory=list)
    dependencies: list[DependencyEdgeResponse] = Field(default_factory=list)
