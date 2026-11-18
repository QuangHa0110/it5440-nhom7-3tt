"""Tiện ích cho các job Jenkins của pr-triage.

    ci_helper.py allowed REPO PR        thoát 0 nếu REPO nằm trong danh sách cho phép
    ci_helper.py poll --state FILE      in PR đang mở có đầu nhánh mới, dạng TSV:
                                        repo, số PR, nhánh đích, sha đầu nhánh

Chỉ dùng thư viện chuẩn. Token GitHub đọc từ biến GITHUB_TOKEN và không bao giờ được in ra.
`poll` ghi trạng thái mới vào FILE.next; job gọi nó đổi tên thành FILE sau khi đã kích build xong.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WILDCARD = re.compile(r"[*?\[]")
API = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")

Fetch = Callable[[str, str], Any]


def patterns(env: Mapping[str, str] | None = None) -> list[str]:
    raw = (os.environ if env is None else env).get("PR_TRIAGE_ALLOWED_REPOS", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


def repo_allowed(repo: str, pats: list[str]) -> bool:
    # Cùng quy ước khớp mẫu với GitHub App (app/settings.py), trừ một điểm:
    # danh sách trống nghĩa là KHÔNG repo nào, vì webhook cấp tổ chức gửi sự kiện của mọi repo.
    return any(fnmatchcase(repo.lower(), p.lower()) for p in pats)


def changed(
    prs_by_repo: Mapping[str, list[dict[str, Any]]],
    state: Mapping[str, str],
    failed: set[str],
) -> tuple[list[tuple[str, str, str, str]], dict[str, str]]:
    """PR cần quét (đầu nhánh khác lần trước) và trạng thái mới.

    PR đã đóng rơi khỏi trạng thái. Repo hỏi lỗi giữ nguyên trạng thái cũ,
    để lần sau không quét lại cả loạt.
    """
    todo: list[tuple[str, str, str, str]] = []
    new_state = {k: v for k, v in state.items() if k.split("#", 1)[0] in failed}
    for repo, prs in prs_by_repo.items():
        for pr in prs:
            if pr.get("draft"):
                continue
            key, sha = f"{repo}#{pr['number']}", pr["head"]["sha"]
            new_state[key] = sha
            if state.get(key) != sha:
                todo.append((repo, str(pr["number"]), pr["base"]["ref"], sha))
    return todo, new_state


def get_json(url: str, token: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pr-triage-jenkins",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def open_prs(repo: str, token: str, fetch: Fetch = get_json) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for page in range(1, 11):
        items = fetch(f"{API}/repos/{repo}/pulls?state=open&per_page=100&page={page}", token)
        out.extend(items)
        if len(items) < 100:
            break
    return out


def cmd_allowed(args: argparse.Namespace) -> int:
    if not REPO_RE.match(args.repo) or not args.pr.isdigit():
        print(f"Tham số không hợp lệ: REPO={args.repo!r} PR={args.pr!r}", file=sys.stderr)
        return 2
    if not repo_allowed(args.repo, patterns()):
        print(f"{args.repo} không nằm trong PR_TRIAGE_ALLOWED_REPOS, bỏ qua.", file=sys.stderr)
        return 1
    return 0


def cmd_poll(args: argparse.Namespace, fetch: Fetch = get_json) -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Thiếu GITHUB_TOKEN.", file=sys.stderr)
        return 2
    pats = patterns()
    if not pats:
        print("PR_TRIAGE_ALLOWED_REPOS trống: không có repo nào để hỏi.", file=sys.stderr)
    state_path = Path(args.state)
    state = json.loads(state_path.read_text("utf-8")) if state_path.exists() else {}
    prs_by_repo: dict[str, list[dict[str, Any]]] = {}
    failed: set[str] = set()
    for repo in pats:
        if WILDCARD.search(repo) or not REPO_RE.match(repo):
            print(f"Bỏ qua mẫu '{repo}': cần tên đầy đủ owner/repo.", file=sys.stderr)
            continue
        try:
            prs_by_repo[repo] = open_prs(repo, token, fetch)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            code = getattr(exc, "code", None) or type(exc).__name__
            print(f"{repo}: không hỏi được GitHub ({code}).", file=sys.stderr)
            failed.add(repo)
    todo, new_state = changed(prs_by_repo, state, failed)
    nxt = state_path.with_name(state_path.name + ".next")
    nxt.write_text(json.dumps(new_state, indent=1, sort_keys=True), "utf-8")
    for row in todo:
        print("\t".join(row))
    print(f"{len(prs_by_repo)} repo, {len(todo)} PR cần quét.", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ci_helper.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("allowed")
    a.add_argument("repo")
    a.add_argument("pr")
    p = sub.add_parser("poll")
    p.add_argument("--state", required=True)
    args = ap.parse_args(argv)
    return cmd_allowed(args) if args.cmd == "allowed" else cmd_poll(args)


if __name__ == "__main__":
    sys.exit(main())
