import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class FindingSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class StaticAnalysisFinding(Base, TimestampMixin):
    __tablename__ = "static_analysis_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=True)
    column: Mapped[int] = mapped_column(Integer, nullable=True)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    analyzer: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity), default=FindingSeverity.MEDIUM, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Text] = mapped_column(Text, nullable=False)
    code_snippet: Mapped[Text] = mapped_column(Text, nullable=True)

    analysis = relationship("AnalysisJob", back_populates="findings")
