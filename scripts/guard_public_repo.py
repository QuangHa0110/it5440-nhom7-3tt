"""Chặn dữ liệu nhạy cảm vào repo public (hook pre-commit và CI).

Danh sách cấm (tên công ty Z, dự án nội bộ...) KHÔNG nằm trong repo. Đọc từ file
trỏ bởi biến PUBLIC_REPO_BLOCKLIST, mặc định ~/.config/pr-triage/blocklist.txt,
mỗi dòng một cụm từ, không phân biệt hoa thường. Không có file thì bỏ qua phần này.
"""

import os
import sys
from pathlib import Path

ALLOWED_IN_DATA = {"data/README.md"}


def load_blocklist() -> list[str]:
    default = Path.home() / ".config" / "pr-triage" / "blocklist.txt"
    path = Path(os.environ.get("PUBLIC_REPO_BLOCKLIST", default))
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip().lower() for line in lines if line.strip()]


def main(files: list[str]) -> int:
    blocklist = load_blocklist()
    problems: list[str] = []
    for name in files:
        rel = Path(name).as_posix()
        if rel.startswith("data/") and rel not in ALLOWED_IN_DATA:
            problems.append(f"{rel}: data/ chỉ được chứa README.md")
            continue
        try:
            text = Path(name).read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            continue
        problems.extend(f"{rel}: chứa cụm bị cấm" for term in blocklist if term in text)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
