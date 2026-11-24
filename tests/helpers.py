"""Tiện ích dựng repo Git thử từ fixture."""

import shutil
import subprocess
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample_java"
REPO_ROOT = Path(__file__).resolve().parents[1]
RULES = REPO_ROOT / "configs" / "semgrep" / "java-injection.yml"


def git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-c", "user.email=t@example.org", "-c", "user.name=t", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def make_repo(dest: Path) -> Path:
    shutil.copytree(FIXTURE / "src", dest / "src")
    git(dest, "init", "-q", "-b", "main")
    git(dest, "add", "-A")
    git(dest, "commit", "-qm", "init")
    return dest
