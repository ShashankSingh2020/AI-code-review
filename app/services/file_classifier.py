from pathlib import Path
from typing import Dict, List
from app.core.config import settings

IGNORED_DIRECTORIES = {
    ".git", "__pycache__", "venv", ".venv", "env",
    "node_modules", ".pytest_cache", ".ruff_cache",
    ".idea", ".vscode", "dist", "build", ".mypy_cache"
}

IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg",
    ".gif", ".ico", ".svg", ".zip", ".tar", ".gz",
    ".pdf", ".exe", ".dll", ".so", ".dylib", ".bin"
}


class FileClassifierService:
    @staticmethod
    def classify_repository(repo_path: Path) -> Dict[str, List[Path]]:
        python_files: List[Path] = []
        skipped_files: List[Path] = []
        total_count = 0

        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue

            if any(part in IGNORED_DIRECTORIES for part in path.parts):
                continue

            if path.suffix.lower() in IGNORED_EXTENSIONS:
                skipped_files.append(path)
                continue

            try:
                if path.stat().st_size > settings.MAX_SINGLE_FILE_BYTES:
                    skipped_files.append(path)
                    continue
            except OSError:
                continue

            total_count += 1
            if total_count > settings.MAX_REPO_FILES:
                break

            if path.suffix.lower() == ".py":
                python_files.append(path)

        return {
            "python_files": python_files,
            "skipped_files": skipped_files
        }
