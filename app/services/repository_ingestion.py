import asyncio
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Tuple

from app.core.config import settings


class IngestionError(Exception):
    """Raised when repository ingestion fails boundary or network checks."""
    pass


def _force_remove_readonly(func, path, exc_info):
    """Windows-safe error handler for read-only Git objects."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _sync_clone(url_str: str, target_dir: Path, timeout_seconds: int):
    cmd = [
        "git",
        "clone",
        "--depth", "1",
        "--single-branch",
        url_str,
        str(target_dir)
    ]
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_seconds
    )
    if res.returncode != 0:
        raise IngestionError(f"Git clone failed: {res.stderr.strip()}")


class RepositoryIngestionService:
    @staticmethod
    def extract_repo_name(repo_url: str) -> str:
        clean_url = str(repo_url).rstrip("/")
        name = clean_url.split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

    @classmethod
    async def clone_repository(cls, repo_url: str, job_id: str) -> Path:
        target_dir = Path(settings.TEMP_STORAGE_PATH) / job_id

        if target_dir.exists():
            shutil.rmtree(target_dir, onerror=_force_remove_readonly)
        target_dir.mkdir(parents=True, exist_ok=True)

        url_str = str(repo_url)

        try:
            await asyncio.to_thread(_sync_clone, url_str, target_dir, settings.CLONE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            cls.cleanup_repository(job_id)
            raise IngestionError(f"Clone timed out after {settings.CLONE_TIMEOUT_SECONDS}s")
        except IngestionError:
            cls.cleanup_repository(job_id)
            raise
        except Exception as e:
            cls.cleanup_repository(job_id)
            raise IngestionError(f"Unexpected error during clone: {str(e)}")

        cls._enforce_size_limit(target_dir)
        return target_dir

    @classmethod
    def _enforce_size_limit(cls, target_dir: Path) -> None:
        total_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
        max_bytes = settings.MAX_REPO_SIZE_MB * 1024 * 1024
        if total_size > max_bytes:
            cls.cleanup_repository(target_dir.name)
            raise IngestionError(
                f"Repository size ({total_size / (1024*1024):.1f}MB) exceeds "
                f"maximum limit of {settings.MAX_REPO_SIZE_MB}MB"
            )

    @classmethod
    def cleanup_repository(cls, job_id: str) -> None:
        target_dir = Path(settings.TEMP_STORAGE_PATH) / job_id
        if target_dir.exists():
            shutil.rmtree(target_dir, onerror=_force_remove_readonly)
