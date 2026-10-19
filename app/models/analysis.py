import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisJob(Base, TimestampMixin):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_url: Mapped[str] = mapped_column(String(512), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), default="repository", nullable=False)
    branch_name: Mapped[str] = mapped_column(String(128), default="main", nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(100), default="QUEUED", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Structural & aggregated metadata
    metrics_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    raw_structural_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    raw_findings: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    raw_dependencies: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    ai_summary: Mapped[str] = mapped_column(Text, default="", nullable=True)

    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optional relationships to granular child tables (if configured)
    findings = relationship("StaticAnalysisFinding", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin")
    edges = relationship("DependencyEdge", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin")
