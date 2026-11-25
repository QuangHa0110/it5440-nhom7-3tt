"""Lọc PR cho cách A theo hai tầng (hướng dẫn chọn repo và PR, bước 3), nhanh hơn `pr-triage replay`.

`replay` quét toàn repo hai lần (base, head) cho mọi commit, mất vài phút mỗi commit trên repo lớn, trong khi
phần lớn commit không sinh cảnh báo mới. Luật Semgrep CE chỉ phân tích trong phạm vi một file, nên cảnh báo
mới (head trừ base) chỉ có thể nằm ở file mà commit sửa. Vì vậy:

1. `prefilter`: với mỗi commit first-parent có 1..N dòng `*.java` thay đổi (P3, P4), lấy nội dung base và head
   của các file thay đổi, quét chung một lượt bằng đúng bộ luật đã khóa (kiểm mã băm như pipeline), rồi so
   multiset (file, luật, đoạn mã) giữa head và base. Commit có chênh lệch là ứng viên. Không bỏ file nào khi
   quét, nên tập ứng viên là tập trên của tập commit có cảnh báo mới.
2. `replay`: chạy pipeline của nhóm (giống hệt `pr-triage replay`: `plan_replay`, `build_pipeline`, tên file
   `replay-<sha>-merged.json`) chỉ trên các ứng viên. Số cảnh báo mới chính thức lấy từ tầng này.

    uv run python scripts/filter_prs.py prefilter --repo data/raw/<ma-repo> --scan-back 600 \\
        --out data/raw/<ma-repo>-loc
    uv run python scripts/filter_prs.py replay --repo data/raw/<ma-repo> --repo-alias <ma-repo> \\
        --candidates data/raw/<ma-repo>-loc/candidates.txt --scan-back 600 --no-secrets \\
        --db data/raw/<ma-repo>-a.sqlite --out data/raw/<ma-repo>-a
    uv run python scripts/summarize_runs.py data/raw/<ma-repo>-a/replay-*.json > data/raw/<ma-repo>-loc-a.tsv
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import json
import shutil
import subprocess
import sys
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from pr_triage import cli
from pr_triage.core.models import RunMode
from pr_triage.pipeline import result_io
from pr_triage.pipeline.build import BuildOptions, build_pipeline
from pr_triage.pipeline.replay import plan_replay
from pr_triage.scan.rulesets import verify_rules

MAX_FILE_BYTES = 1_000_000  # bằng --max-target-bytes mặc định của Semgrep
Key = tuple[str, str, str]  # (đường dẫn trong repo, luật, đoạn mã đã chuẩn hóa)


@dataclasses.dataclass(frozen=True)
class Candidate:
    idx: int
    sha: str
    pr: int
    base: str
    head: str
    java_lines: int


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def numstat_lines(text: str) -> int:
    """Tổng dòng thêm và xóa từ `git diff --numstat` (file nhị phân ghi `-`, tính 0)."""
    total = 0
    for line in text.splitlines():
        added, deleted, _ = line.split("\t", 2)
        total += (int(added) if added.isdigit() else 0) + (int(deleted) if deleted.isdigit() else 0)
    return total


def parse_name_status(raw: bytes) -> list[tuple[str, str]]:
    """`git diff --name-status -z --no-renames` thành [(trạng thái, đường dẫn)]."""
    parts = raw.split(b"\0")
    return [
        (parts[i].decode()[:1], parts[i + 1].decode("utf-8", "surrogateescape"))
        for i in range(0, len(parts) - 1, 2)
    ]


def plan(repo: Path, ref: str, scan_back: int, max_java_lines: int) -> list[Candidate]:
    out: list[Candidate] = []
    for item in plan_replay(repo, ref, scan_back, "merged"):
        if item.skip_reason:
            continue
        diff = _git(repo, "diff", "--numstat", item.base, item.head, "--", "*.java").decode()
        n = numstat_lines(diff)
        if 0 < n <= max_java_lines:
            out.append(Candidate(len(out), item.sha, item.pr_number, item.base, item.head, n))
    return out


def _dump(repo: Path, rev: str, path: str, dest: Path) -> bool:
    try:
        data = _git(repo, "show", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return False
    if len(data) > MAX_FILE_BYTES or b"\0" in data[:8000]:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


def materialize(repo: Path, cands: Iterable[Candidate], work: Path) -> None:
    """Ghi file thay đổi của mỗi ứng viên vào `work/<idx>/h/...` (head) và `work/<idx>/b/...` (base)."""
    for c in cands:
        raw = _git(repo, "diff", "--name-status", "-z", "--no-renames", c.base, c.head)
        for status, path in parse_name_status(raw):
            if status in "AMT":
                _dump(repo, c.head, path, work / str(c.idx) / "h" / path)
            if status in "DMT":
                _dump(repo, c.base, path, work / str(c.idx) / "b" / path)


def _norm(text: str) -> str:
    return "\n".join(s.strip() for s in text.splitlines() if s.strip())


def new_by_commit(results: Iterable[dict[str, Any]]) -> dict[int, collections.Counter[Key]]:
    """Từ kết quả JSON của Semgrep trên cây `work`, trả về cảnh báo có ở head mà không có ở base."""
    sides: dict[tuple[int, str], collections.Counter[Key]] = collections.defaultdict(
        collections.Counter
    )
    for r in results:
        idx, side, rel = str(r["path"]).split("/", 2)
        rule = str(r["check_id"]).rsplit(".", 1)[-1]
        sides[(int(idx), side)][(rel, rule, _norm(str(r.get("extra", {}).get("lines", ""))))] += 1
    idxs = {i for i, _ in sides}
    return {i: sides[(i, "h")] - sides[(i, "b")] for i in idxs}


def semgrep(work: Path, rules: Sequence[str], jobs: int, out: Path) -> dict[str, Any]:
    exe = Path(sys.executable).parent / "semgrep"
    cmd = [str(exe) if exe.exists() else "semgrep", "scan", "--json", "--output", str(out)]
    for r in rules:
        cmd += ["--config", str(Path(r).resolve())]
    # --no-git-ignore: thư mục tạm thường nằm trong data/ (bị .gitignore), cây tạm chỉ chứa file đã theo dõi
    cmd += ["--metrics=off", "--quiet", "--disable-version-check", "--timeout", "30"]
    cmd += ["--no-git-ignore", "-j", str(jobs), "."]
    subprocess.run(cmd, cwd=work, check=False)
    data: dict[str, Any] = json.loads(out.read_text("utf-8"))
    return data


def cmd_prefilter(a: argparse.Namespace) -> int:
    t0 = time.monotonic()
    repo, out = a.repo.resolve(), a.out.resolve()
    rules = a.rules or list(BuildOptions().rules)
    verify_rules(rules, Path(a.rules_lock))
    cands = plan(repo, a.ref, a.scan_back, a.max_java_lines)
    work = out / "tree"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    (work / ".semgrepignore").write_text("")  # không bỏ file nào: tập ứng viên là tập trên
    materialize(repo, cands, work)
    data = semgrep(work, rules, a.jobs, out / "semgrep.json")
    new = new_by_commit(data["results"])
    rows = []
    for c in cands:
        diff = new.get(c.idx, collections.Counter())
        java = sum(n for k, n in diff.items() if k[0].endswith(".java"))
        rows.append(
            {
                **dataclasses.asdict(c),
                "pre_new": sum(diff.values()),
                "pre_new_java": java,
                "rules": sorted({k[1] for k in diff}),
            }
        )
    (out / "prefilter.json").write_text(json.dumps(rows, indent=1), "utf-8")
    hits = [r for r in rows if r["pre_new"]]
    (out / "candidates.txt").write_text("".join(f"{r['sha']}\n" for r in hits), "utf-8")
    with (out / "prefilter.tsv").open("w", encoding="utf-8") as fh:
        fh.write("sha\tpr\tjava_lines\tpre_new\tpre_new_java\trules\n")
        for r in rows:
            fh.write(
                f"{r['sha'][:9]}\t{r['pr']}\t{r['java_lines']}\t{r['pre_new']}\t"
                f"{r['pre_new_java']}\t{','.join(r['rules'])}\n"
            )
    summary = {
        "commit_sua_java": len(rows),
        "file_da_quet": len(data["paths"].get("scanned", [])),
        "ung_vien": len(hits),
        "canh_bao_co_the_moi": sum(r["pre_new"] for r in hits),
        "loi_semgrep": len(data.get("errors", [])),
        "thoi_gian_s": round(time.monotonic() - t0),
    }
    print(json.dumps(summary, ensure_ascii=False))
    shutil.rmtree(work, ignore_errors=True)
    return 0


def cmd_replay(a: argparse.Namespace, rest: list[str]) -> int:
    args = cli.parser().parse_args(["replay", *rest, "--count", str(a.scan_back)])
    only = set(a.candidates.read_text("utf-8").split())
    opts = dataclasses.replace(cli._opts(args, RunMode.REPLAY), semgrep_timeout_s=a.semgrep_timeout)
    pipeline, store = build_pipeline(opts)
    args.out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for item in plan_replay(args.repo, args.ref, args.count, args.side):
        if item.skip_reason or item.sha not in only:
            continue
        dest = args.out / f"replay-{item.sha[:8]}-{args.side}.json"
        if dest.exists() and '"status": "failed"' not in dest.read_text("utf-8"):
            continue  # chạy lại được: bỏ qua commit đã có kết quả tốt
        result = pipeline.run(args.repo, item.base, item.head, item.pr_number)
        result_io.write(result, dest)
        print(
            json.dumps(
                {"commit": item.sha[:8], "pr": item.pr_number, **cli.summarize(result)},
                ensure_ascii=False,
            ),
            flush=True,
        )
        failed += result.run.status.value == "failed"
    store.close()
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pre = sub.add_parser("prefilter", help="tầng 1: sàng commit có thể có cảnh báo mới")
    pre.add_argument("--repo", type=Path, required=True)
    pre.add_argument("--ref", default="HEAD")
    pre.add_argument("--scan-back", type=int, default=400, help="số commit first-parent xét lùi")
    pre.add_argument("--max-java-lines", type=int, default=1000, help="P4: bỏ commit sửa quá nhiều")
    pre.add_argument("--rules", action="append", help="file luật (mặc định: bộ luật trong lock)")
    pre.add_argument("--rules-lock", default="configs/semgrep/rulesets.lock")
    pre.add_argument("--jobs", type=int, default=4)
    pre.add_argument("--out", type=Path, required=True)
    rep = sub.add_parser(
        "replay", help="tầng 2: pipeline đầy đủ trên ứng viên; tham số khác như replay"
    )
    rep.add_argument("--candidates", type=Path, required=True, help="candidates.txt của prefilter")
    rep.add_argument("--scan-back", type=int, default=400, help="phải bằng giá trị của prefilter")
    rep.add_argument(
        "--semgrep-timeout",
        type=int,
        default=1200,
        help="trần thời gian cả lượt quét, giây (vận hành, không vào manifest); dự án mặc định 300",
    )
    a, rest = ap.parse_known_args(argv)
    if a.cmd == "prefilter":
        if rest:
            ap.error(f"tham số lạ: {' '.join(rest)}")
        return cmd_prefilter(a)
    return cmd_replay(a, rest)


if __name__ == "__main__":
    raise SystemExit(main())
