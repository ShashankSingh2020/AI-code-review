from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_async_db

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        environment=settings.APP_ENV
    )


@router.get("/health/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_async_db)) -> ReadinessResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    return ReadinessResponse(
        status="ready" if db_status == "connected" else "degraded",
        database=db_status
    )
