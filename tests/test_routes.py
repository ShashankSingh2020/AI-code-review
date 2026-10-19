from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    # Test both root and api health paths
    response = client.get("/health")
    if response.status_code == 404:
        response = client.get("/api/v1/health")
    assert response.status_code == 200

def test_create_analysis_invalid_url():
    payload = {
        "repo_url": "https://notgithub.com/insecure/repo.git",
        "branch_name": "main"
    }
    response = client.post("/api/v1/analyses", json=payload)
    assert response.status_code == 400
    assert "Invalid repository URL" in response.json()["detail"]

def test_get_nonexistent_job_returns_404():
    response = client.get("/api/v1/analyses/non_existent_job_id_123")
    assert response.status_code == 404

def test_fix_endpoint_fallback():
    payload = {
        "rule_id": "AST-E001",
        "message": "Bare except handler",
        "file_path": "test.py",
        "line": 10,
        "code_context": ""
    }
    response = client.post("/api/v1/analyses/fix", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "suggested_patch" in data
