from datetime import datetime
from typing import Any, Dict, List, Optional
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
    line: Optional[int] = None
    column: Optional[int] = None
    rule_id: str
    analyzer: str
    severity: FindingSeverity
    title: str
    message: str
    code_snippet: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DependencyEdgeResponse(BaseModel):
    id: str
    source_node: str
    target_node: str
    edge_type: str
    line_number: Optional[int] = None

    class Config:
        from_attributes = True


class AnalysisJobStatusResponse(BaseModel):
    id: str
    repo_url: str
    repo_name: str
    status: JobStatus
    current_stage: str
    error_message: Optional[str] = None
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompleteAnalysisReportResponse(AnalysisJobStatusResponse):
    findings: List[FindingResponse] = Field(default_factory=list)
    dependencies: List[DependencyEdgeResponse] = Field(default_factory=list)
