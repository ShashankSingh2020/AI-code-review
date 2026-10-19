import re
import shutil
import subprocess
import uuid
from pathlib import Path

from app.core.config import settings

GITHUB_URL_REGEX = re.compile(r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(\.git)?$")

class RepositoryIngestionService:
    def __init__(self, base_storage_dir: str = "storage/cloned_repos"):
        self.base_storage_dir = Path(base_storage_dir)
        self.base_storage_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = getattr(settings, "PIPELINE_TIMEOUT_SECONDS", 120)
        self.max_size_mb = getattr(settings, "MAX_REPO_SIZE_MB", 50)

    def validate_url(self, repo_url: str) -> bool:
        return bool(GITHUB_URL_REGEX.match(repo_url.strip()))

    def _get_dir_size_mb(self, path: Path) -> float:
        total = sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())
        return total / (1024 * 1024)

    def clone_repository(self, repo_url: str, branch_name: str = "main") -> Path:
        clean_url = repo_url.strip()
        if not self.validate_url(clean_url):
            raise ValueError("Invalid GitHub URL. Must be an HTTPS GitHub repository URL.")

        unique_id = str(uuid.uuid4())[:8]
        repo_name = clean_url.rstrip("/").split("/")[-1].replace(".git", "")
        dest_dir = self.base_storage_dir / f"{repo_name}_{unique_id}"

        cmd = [
            "git", "clone",
            "--depth", "1",
            "--branch", branch_name,
            "--single-branch",
            clean_url,
            str(dest_dir)
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=self.timeout)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Fallback: clone default branch if the custom branch fails
            fallback_cmd = ["git", "clone", "--depth", "1", clean_url, str(dest_dir)]
            subprocess.run(fallback_cmd, capture_output=True, text=True, check=True, timeout=self.timeout)

        # Enforce size limits
        size_mb = self._get_dir_size_mb(dest_dir)
        if size_mb > self.max_size_mb:
            self.cleanup(dest_dir)
            raise ValueError(f"Repository size ({size_mb:.1f} MB) exceeds maximum allowed limit ({self.max_size_mb} MB).")

        return dest_dir

    def cleanup(self, path: Path):
        if path and Path(path).exists():
            shutil.rmtree(path, ignore_errors=True)

repo_ingestion_service = RepositoryIngestionService()
