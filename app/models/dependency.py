import uuid
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DependencyEdge(Base, TimestampMixin):
    __tablename__ = "dependency_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    source_node: Mapped[str] = mapped_column(String(512), nullable=False)
    target_node: Mapped[str] = mapped_column(String(512), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(50), default="IMPORT", nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=True)

    analysis = relationship("AnalysisJob", back_populates="edges")
