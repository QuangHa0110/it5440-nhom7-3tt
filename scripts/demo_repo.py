"""Dựng repo demo: nhánh main sạch và mỗi kịch bản một nhánh (và một PR nếu có --repo).

Chạy thử cục bộ, không đụng tới GitHub:   python scripts/demo_repo.py --workdir /tmp/demo --dry-run
Đẩy lên GitHub (repo trống do bạn tạo):   python scripts/demo_repo.py --workdir /tmp/demo --repo OWNER/NAME
Cần: git đã đăng nhập (SSH hoặc token) và `gh auth login` để mở PR. App phải được cài lên repo trước.
"""

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "demo" / "base"
SCENARIOS = ROOT / "demo" / "scenarios"


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    body: str


def scenarios(only: list[str] | None = None) -> list[Scenario]:
    out: list[Scenario] = []
    for d in sorted(p for p in SCENARIOS.iterdir() if p.is_dir()):
        if only and not any(o in d.name for o in only):
            continue
        text = (d / "pr.md").read_text("utf-8").strip().split("\n", 1)
        out.append(Scenario(d.name, text[0], text[1].strip() if len(text) > 1 else ""))
    return out


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.email=demo@example.org", "-c", "user.name=Demo Outsourcer", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    )  # fmt: skip
    return proc.stdout.strip()


def build(workdir: Path, only: list[str] | None = None) -> list[Scenario]:
    """Tạo kho cục bộ: main từ demo/base, mỗi kịch bản một nhánh tách từ main."""
    if workdir.exists() and any(workdir.iterdir()):
        raise SystemExit(f"{workdir} không trống, chọn thư mục khác")
    workdir.mkdir(parents=True, exist_ok=True)
    git(workdir, "init", "-q", "-b", "main")
    shutil.copytree(BASE, workdir, dirs_exist_ok=True)
    git(workdir, "add", "-A")
    git(workdir, "commit", "-qm", "chore: ứng dụng mẫu ban đầu")
    chosen = scenarios(only)
    for sc in chosen:
        git(workdir, "switch", "-q", "main")
        git(workdir, "switch", "-qc", f"demo/{sc.name}")
        shutil.copytree(SCENARIOS / sc.name / "files", workdir, dirs_exist_ok=True)
        git(workdir, "add", "-A")
        git(workdir, "commit", "-qm", sc.title)
    git(workdir, "switch", "-q", "main")
    return chosen


def publish(workdir: Path, repo: str, chosen: list[Scenario]) -> None:
    git(workdir, "remote", "add", "origin", f"https://github.com/{repo}.git")
    git(workdir, "push", "-u", "origin", "main")
    for sc in chosen:
        branch = f"demo/{sc.name}"
        git(workdir, "push", "-u", "origin", branch)
        subprocess.run(
            ["gh", "pr", "create", "--repo", repo, "--base", "main", "--head", branch,
             "--title", sc.title, "--body", sc.body],
            cwd=workdir, check=True,
        )  # fmt: skip
        print(f"đã mở PR cho {sc.name}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--workdir", type=Path, required=True)
    ap.add_argument("--repo", help="OWNER/NAME của repo GitHub trống để đẩy lên")
    ap.add_argument("--dry-run", action="store_true", help="chỉ dựng kho cục bộ")
    ap.add_argument("--only", action="append", help="chỉ chạy kịch bản có tên chứa chuỗi này")
    args = ap.parse_args(argv)
    if not args.dry_run and not args.repo:
        print("cần --repo OWNER/NAME hoặc --dry-run", file=sys.stderr)
        return 2
    chosen = build(args.workdir, args.only)
    print(
        f"đã dựng {args.workdir} với {len(chosen)} nhánh: "
        + ", ".join(f"demo/{s.name}" for s in chosen)
    )
    if args.dry_run:
        return 0
    publish(args.workdir, args.repo, chosen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
