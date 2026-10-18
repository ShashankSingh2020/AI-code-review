from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.schemas.fix import FixRequest, FixResponse
from app.services.fixer import fixer_service

router = APIRouter(prefix="/analyses", tags=["analyses"])

SCAN_HISTORY = [
    {
        "job_id": "job_demo_101",
        "repo_url": "https://github.com/octocat/Hello-World.git",
        "branch_name": "main",
        "status": "COMPLETED",
        "structural_metrics": {"file_count": 14, "function_count": 82},
        "findings": [
            {
                "rule_id": "E722",
                "severity": "HIGH",
                "file_path": "core/processor.py",
                "line": 42,
                "title": "Do not use bare except",
                "message": "Catch specific exceptions instead of bare except"
            },
            {
                "rule_id": "F401",
                "severity": "LOW",
                "file_path": "utils/helpers.py",
                "line": 5,
                "title": "Unused import",
                "message": "sys imported but unused"
            },
            {
                "rule_id": "RADON_COMPLEXITY",
                "severity": "MEDIUM",
                "file_path": "api/routes.py",
                "line": 118,
                "title": "Cyclomatic Complexity High (Grade D)",
                "message": "Function dispatch_event has cyclomatic complexity higher than 15"
            }
        ],
        "dependencies": [
            {
                "source_node": "core.processor",
                "target_node": "typing.Optional",
                "edge_type": "import",
                "line_number": 2
            },
            {
                "source_node": "api.routes",
                "target_node": "fastapi.APIRouter",
                "edge_type": "import",
                "line_number": 1
            }
        ],
        "ai_summary": "Architecture Review: Codebase structure is sound. Critical issue detected in core/processor.py with bare except.",
        "created_at": "2026-10-19T01:00:00Z"
    }
]

@router.get("", response_model=dict)
async def get_scan_history(db: AsyncSession = Depends(get_async_db)):
    results = [
        {
            "job_id": item["job_id"],
            "repo_url": item["repo_url"],
            "branch_name": item["branch_name"],
            "status": item["status"],
            "total_files": item["structural_metrics"]["file_count"],
            "total_findings": len(item["findings"]),
            "created_at": item["created_at"]
        }
        for item in SCAN_HISTORY
    ]
    return {"history": results}

@router.get("/{job_id}", response_model=dict)
async def get_scan_by_id(job_id: str, db: AsyncSession = Depends(get_async_db)):
    for item in SCAN_HISTORY:
        if item["job_id"] == job_id:
            return item
    raise HTTPException(status_code=404, detail="Scan not found")

@router.post("", response_model=dict)
async def create_analysis(payload: dict, db: AsyncSession = Depends(get_async_db)):
    repo_url = payload.get("repo_url", "")
    branch_name = payload.get("branch_name", "main")
    new_job_id = f"job_{len(SCAN_HISTORY) + 101}"
    new_scan = {
        "job_id": new_job_id,
        "repo_url": repo_url,
        "branch_name": branch_name,
        "status": "COMPLETED",
        "structural_metrics": {"file_count": 14, "function_count": 82},
        "findings": [
            {
                "rule_id": "E722",
                "severity": "HIGH",
                "file_path": "core/processor.py",
                "line": 42,
                "title": "Do not use bare except",
                "message": "Catch specific exceptions instead of bare except"
            },
            {
                "rule_id": "F401",
                "severity": "LOW",
                "file_path": "utils/helpers.py",
                "line": 5,
                "title": "Unused import",
                "message": "sys imported but unused"
            },
            {
                "rule_id": "RADON_COMPLEXITY",
                "severity": "MEDIUM",
                "file_path": "api/routes.py",
                "line": 118,
                "title": "Cyclomatic Complexity High (Grade D)",
                "message": "Function dispatch_event has cyclomatic complexity higher than 15"
            }
        ],
        "dependencies": [
            {
                "source_node": "core.processor",
                "target_node": "typing.Optional",
                "edge_type": "import",
                "line_number": 2
            },
            {
                "source_node": "api.routes",
                "target_node": "fastapi.APIRouter",
                "edge_type": "import",
                "line_number": 1
            }
        ],
        "ai_summary": "Architecture Review: Codebase structure is sound. Critical issue detected in core/processor.py with bare except.",
        "created_at": "2026-10-19T01:00:00Z"
    }
    SCAN_HISTORY.insert(0, new_scan)
    return new_scan

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