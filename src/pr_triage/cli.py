"""Điểm vào dòng lệnh `pr-triage`."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from pr_triage import __version__
from pr_triage.bot import FeedbackCollector, Publisher, render, resolve_states
from pr_triage.bot.github import GitHubScm
from pr_triage.core.alias import Aliaser
from pr_triage.core.models import PrRef, RunMode, TriageResult, Variant
from pr_triage.pipeline import result_io
from pr_triage.pipeline.build import BuildOptions, build_pipeline
from pr_triage.pipeline.gitrepo import first_parent_commits, parents


def load_dotenv(path: Path = Path(".env")) -> None:
    """Nạp .env nếu có, không ghi đè biến môi trường đã đặt. Không bao giờ in giá trị."""
    if not path.is_file():
        return
    for line in path.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--repo", type=Path, default=Path("."), help="repo Git cục bộ")
    p.add_argument("--repo-alias", default="repo")
    p.add_argument("--db", default="data/dev/store.sqlite")
    p.add_argument("--rules", action="append", help="file luật Semgrep (lặp được)")
    p.add_argument("--catalog", default="configs/context/java.yml")
    p.add_argument("--display", choices=["A", "B", "C"], default="B")
    p.add_argument("--engine", choices=["graph", "plain"], default="graph")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--out", type=Path, default=Path("out"))


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="pr-triage", description=__doc__)
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd")
    run = sub.add_parser("run", help="quét và nhận định một PR (job triage)")
    _common(run)
    run.add_argument("--base", required=True)
    run.add_argument("--head", required=True)
    run.add_argument("--pr", type=int, required=True)
    run.add_argument("--mode", choices=[m.value for m in RunMode], default="shadow")
    pub = sub.add_parser("publish", help="đăng hoặc cập nhật comment (job publish)")
    pub.add_argument("--result", type=Path, required=True)
    pub.add_argument("--slug", required=True, help="owner/repo trên GitHub")
    pub.add_argument("--pr", type=int, required=True)
    pub.add_argument("--db", default="data/dev/store.sqlite")
    pub.add_argument(
        "--post", action="store_true", help="đăng thật. Mặc định chỉ in comment (dry-run)"
    )
    fb = sub.add_parser("feedback", help="thu phản hồi của lập trình viên (job feedback)")
    fb.add_argument("--result", type=Path, required=True)
    fb.add_argument("--slug", required=True)
    fb.add_argument("--pr", type=int, required=True)
    fb.add_argument("--comment-ref", required=True)
    fb.add_argument("--db", default="data/dev/store.sqlite")
    rep = sub.add_parser("replay", help="chạy lại trên các commit đã merge gần đây")
    _common(rep)
    rep.add_argument("--ref", default="HEAD")
    rep.add_argument("--count", type=int, default=10)
    return ap


def _opts(args: argparse.Namespace, mode: RunMode) -> BuildOptions:
    kw: dict[str, object] = {
        "catalog": args.catalog,
        "db": args.db,
        "repo_alias": args.repo_alias,
        "mode": mode,
        "display": Variant(args.display),
        "engine": args.engine,
        "workers": args.workers,
    }
    if args.rules:
        kw["rules"] = args.rules
    return BuildOptions(**kw)  # type: ignore[arg-type]


def summarize(result: TriageResult) -> dict[str, object]:
    verdicts = Counter(f"{v.variant.value}:{v.label.value}" for v in result.verdicts)
    return {
        "run_id": result.run.run_id,
        "status": result.run.status.value,
        "new_findings": len(result.findings),
        "verdicts": dict(sorted(verdicts.items())),
        "tokens_in": sum(v.tokens_in for v in result.verdicts),
        "tokens_out": sum(v.tokens_out for v in result.verdicts),
        "errors": len(result.errors),
        "duration_s": result.run.duration_s,
    }


def _publish(args: argparse.Namespace) -> int:
    from pr_triage.store import SqlStore

    result = result_io.read(args.result)
    store = SqlStore(args.db)
    pr = PrRef(args.slug, args.pr, result.run.head_sha, result.run.base_sha)
    if not args.post:
        print(render(result))
        return 0
    scm = GitHubScm(os.environ["GITHUB_TOKEN"])
    ref = Publisher(scm, store).publish(result, pr, post=True)
    print(json.dumps({"comment_ref": ref, "mode": result.run.mode.value}))
    store.close()
    return 0


def _feedback(args: argparse.Namespace) -> int:
    from pr_triage.store import SqlStore

    result = result_io.read(args.result)
    store = SqlStore(args.db)
    pr = PrRef(args.slug, args.pr, result.run.head_sha, result.run.base_sha)
    salt = os.environ.get("PR_TRIAGE_ALIAS_SALT", "")
    if not salt:
        print("thiếu PR_TRIAGE_ALIAS_SALT (muối bí danh, giữ trong Z)", file=sys.stderr)
        return 2
    scm = GitHubScm(os.environ["GITHUB_TOKEN"])
    events = FeedbackCollector(scm, store, Aliaser(salt)).collect(result, pr, args.comment_ref)
    closed = scm.pr_state(pr) != "open"
    for alert in resolve_states(
        result.displayed, store.list_feedback(result.run.run_id), closed=closed
    ):
        store.save_displayed(alert)
    print(json.dumps({"new_events": len(events), "closed": closed}))
    store.close()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    args = parser().parse_args(argv)
    if args.cmd == "run":
        pipeline, store = build_pipeline(_opts(args, RunMode(args.mode)))
        result = pipeline.run(args.repo, args.base, args.head, args.pr)
        result_io.write(result, args.out / "triage-result.json")
        store.close()
        print(json.dumps(summarize(result), ensure_ascii=False))
        return 1 if result.run.status.value == "failed" else 0
    if args.cmd == "publish":
        return _publish(args)
    if args.cmd == "feedback":
        return _feedback(args)
    if args.cmd == "replay":
        pipeline, store = build_pipeline(_opts(args, RunMode.REPLAY))
        failed = 0
        for i, sha in enumerate(first_parent_commits(args.repo, args.ref, args.count), 1):
            ps = parents(args.repo, sha)
            if not ps:
                continue
            base, head = (ps[0], ps[1]) if len(ps) > 1 else (ps[0], sha)
            result = pipeline.run(args.repo, base, head, i)
            result_io.write(result, args.out / f"replay-{sha[:8]}.json")
            print(json.dumps({"commit": sha[:8], **summarize(result)}, ensure_ascii=False))
            failed += result.run.status.value == "failed"
        store.close()
        return 1 if failed else 0
    parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
