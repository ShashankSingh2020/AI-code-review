from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.routes.analyses import router as analyses_router
from app.api.v1.routes.health import router as health_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import async_engine
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.TEMP_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    # Automatically initialize tables in Neon PostgreSQL on startup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Ensure new columns exist on already-created tables
        await conn.execute(text("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS branch_name VARCHAR(128) DEFAULT 'main';"))
        await conn.execute(text("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS raw_structural_metrics JSON DEFAULT '{}';"))
        await conn.execute(text("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS raw_findings JSON DEFAULT '[]';"))
        await conn.execute(text("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS raw_dependencies JSON DEFAULT '[]';"))
        await conn.execute(text("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS ai_summary TEXT DEFAULT '';"))

    yield

    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health check for monitoring, load balancers, and test suites
@app.get("/health", tags=["system"])
async def root_health():
    return {"status": "healthy"}

# Versioned routes
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(analyses_router, prefix=settings.API_V1_STR)