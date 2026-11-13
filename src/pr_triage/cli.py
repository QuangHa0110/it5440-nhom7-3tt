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
from pr_triage.core.models import HumanLabel, PrRef, RunMode, TriageResult, Variant
from pr_triage.core.ports import StorePort
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
    p.add_argument("--no-secrets", action="store_true", help="tắt quét secret")
    p.add_argument(
        "--snippet-radius", type=int, default=10, help="số dòng quanh vị trí báo của cách B"
    )
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
    ev = sub.add_parser("eval", help="luồng đánh giá ngoại tuyến (chạy trong vùng của Z)")
    ev.add_argument("--db", default="data/dev/store.sqlite")
    es = ev.add_subparsers(dest="eval_cmd")
    p = es.add_parser("pool", help="dựng tập cảnh báo, tách dev và eval")
    p.add_argument("--cutoff", required=True, help="thời điểm ISO: PR bắt đầu từ đây vào eval")
    p.add_argument("--eval-only-repo", action="append", default=[])
    p = es.add_parser("label-export", help="xuất phiếu gán nhãn mù")
    p.add_argument("--split", choices=["dev", "eval"], required=True)
    p.add_argument("--labelers", required=True, help="tên cách nhau bằng dấu phẩy, ít nhất hai")
    p.add_argument("--out", type=Path, default=Path("data/dev/labels"))
    p.add_argument("--seed", type=int, default=0)
    p = es.add_parser("label-import", help="nhập phiếu đã điền")
    p.add_argument("--labeler", required=True)
    p.add_argument("--file", type=Path, required=True)
    es.add_parser("kappa", help="Cohen's kappa giữa hai người gán nhãn")
    es.add_parser("finalize", help="chốt các ca đồng ý, in hàng đợi phân xử")
    p = es.add_parser("adjudicate", help="nhập nhãn phân xử cho một cảnh báo")
    p.add_argument("--finding", required=True)
    p.add_argument("--value", choices=[h.value for h in HumanLabel], required=True)
    p.add_argument("--who", required=True)
    p.add_argument("--z", action="store_true", help="đã được kỹ sư của Z xác minh")
    p = es.add_parser("freeze", help="khóa cấu hình thành manifest")
    p.add_argument("--manifest", type=Path, default=Path("configs/eval/manifest.json"))
    p = es.add_parser("metrics", help="tính số đo")
    p.add_argument("--split", choices=["dev", "eval"], required=True)
    p.add_argument("--manifest", type=Path, default=Path("configs/eval/manifest.json"))
    p.add_argument("--rounds", type=int, default=1000)
    p.add_argument("--markdown", action="store_true")
    p = es.add_parser("export", help="xuất số liệu tổng hợp ẩn danh")
    p.add_argument("--split", choices=["dev", "eval"], required=True)
    p.add_argument("--out", type=Path, default=Path("reports/results/summary.json"))
    p.add_argument("--k", type=int, default=5)
    srv = sub.add_parser("serve", help="chạy GitHub App (máy chủ webhook)")
    srv.add_argument("--host", default="0.0.0.0")
    srv.add_argument("--port", type=int, default=8080)
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
        "snippet_radius": args.snippet_radius,
        "secrets": not args.no_secrets,
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


def _manifest_roots() -> list[Path]:
    return [Path("configs/semgrep"), Path("configs/context"), Path("configs/schemas"),
            Path("configs/eval/thresholds.yml")]  # fmt: skip


def _current_manifest() -> dict[str, object]:
    from pr_triage.evaluation import compute_manifest
    from pr_triage.llm.prompt import PROMPT_VERSION

    extra = {"prompt_version": PROMPT_VERSION, "model": os.environ.get("PR_TRIAGE_LLM_MODEL", "")}
    return compute_manifest([r for r in _manifest_roots() if r.exists()], extra)


def _forbidden(store: StorePort) -> set[str]:
    terms: set[str] = set()
    for e in store.list_pool():
        f = store.get_finding(e.finding_id)
        terms.add(e.finding_id)
        if f is not None:
            terms.add(f.file)
    default = Path.home() / ".config/pr-triage/blocklist.txt"
    bl = Path(os.environ.get("PUBLIC_REPO_BLOCKLIST", default))
    if bl.is_file():
        terms.update(x.strip() for x in bl.read_text("utf-8").splitlines() if x.strip())
    return terms


def _eval(args: argparse.Namespace) -> int:
    from pr_triage.evaluation import (
        FreezeMismatch,
        blind,
        build_pool,
        check_manifest,
        compute_report,
        to_markdown,
        write_manifest,
    )
    from pr_triage.evaluation import adjudicate as adj
    from pr_triage.evaluation.export import assert_clean, export_summary
    from pr_triage.store import SqlStore

    store = SqlStore(args.db)
    try:
        cmd = args.eval_cmd
        if cmd == "pool":
            entries = build_pool(store, args.cutoff, args.eval_only_repo)
            print(json.dumps({"dev": sum(e.split == "dev" for e in entries),
                              "eval": sum(e.split == "eval" for e in entries)}))  # fmt: skip
        elif cmd == "label-export":
            paths = blind.export_sheets(
                store, args.split, args.labelers.split(","), args.out, args.seed
            )
            print(json.dumps({k: str(v) for k, v in paths.items()}, ensure_ascii=False))
        elif cmd == "label-import":
            print(json.dumps({"imported": blind.import_sheet(store, args.labeler, args.file)}))
        elif cmd == "kappa":
            k = adj.kappa(store)
            print(json.dumps({"kappa": k.kappa, "n": k.n, "min": adj.KAPPA_MIN}))
        elif cmd == "finalize":
            n = adj.finalize_agreed(store)
            print(json.dumps({"finalized": n, "queue": adj.queue(store)}))
        elif cmd == "adjudicate":
            adj.adjudicate(store, args.finding, HumanLabel(args.value), args.who, args.z)
            print(json.dumps({"ok": True}))
        elif cmd == "freeze":
            write_manifest(_current_manifest(), args.manifest)
            print(f"đã ghi {args.manifest}. Commit rồi gắn tag: git tag eval-freeze-<n>")
        elif cmd == "metrics":
            if args.split == "eval":
                check_manifest(args.manifest, _current_manifest())
            report = compute_report(store, args.split, args.rounds)
            print(
                to_markdown(report)
                if args.markdown
                else json.dumps(report, ensure_ascii=False, indent=2)
            )
        elif cmd == "export":
            summary = export_summary(compute_report(store, args.split, 200), args.k)
            assert_clean(summary, _forbidden(store))
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", "utf-8")
            print(f"đã ghi {args.out}")
        else:
            print(
                "dùng: pr-triage eval {pool|label-export|label-import|kappa|finalize|"
                "adjudicate|freeze|metrics|export}"
            )
            return 0
    except (FreezeMismatch, adj.KappaTooLow, blind.SheetError) as exc:
        print(f"từ chối: {exc}", file=sys.stderr)
        return 3
    finally:
        store.close()
    return 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    from pr_triage.app.server import build_services, create_app
    from pr_triage.app.settings import SettingsError

    try:
        services = build_services()
    except SettingsError as exc:
        print(f"không khởi động được: {exc}", file=sys.stderr)
        return 2
    logging.getLogger("pr_triage").setLevel(logging.INFO)
    uvicorn.run(create_app(services), host=args.host, port=args.port, log_level="info")
    return 0


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
    if args.cmd == "serve":
        return _serve(args)
    if args.cmd == "eval":
        return _eval(args)
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
