"""Tổng hợp gói nộp của các thành viên (hướng dẫn chọn repo và PR, bước 7) thành bảng Markdown.

Mỗi gói là một thư mục chứa `<ma-repo>-run/<pr>/triage-result.json` (đầu ra `pr-triage run --out`). Thư mục có
đuôi `-loi` bị bỏ qua (kết quả cũ chỉ để đối chiếu). Đối số có dạng `<thanh-vien>=<thu-muc>`:

    uv run python scripts/tong_hop_so_lieu.py sonnh95=data/raw/sonnh95/gon/sonnh95-2026-11-25 > tong-hop.md

`--mu` bỏ mọi số theo nhãn B, C để người sắp gán nhãn đáp án xem được mà không mất mù. Script chỉ đọc, không ghi
gì. Đầu ra chứa số đếm, không chứa đoạn mã hay giải thích của LLM.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import io
import json
import statistics
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from pr_triage.evaluation.metrics import wilson

VARIANTS = ("B", "C")
LABELS = ("likely_true", "likely_false", "unknown", "invalid", "loi_ha_tang")


@dataclasses.dataclass(frozen=True)
class Alert:
    member: str
    repo: str
    pr: int
    rule: str
    java: bool
    labels: dict[str, str]


@dataclasses.dataclass(frozen=True)
class Run:
    member: str
    repo: str
    pr: int
    status: str
    manifest: str
    duration_s: float
    tokens: int
    latencies_ms: tuple[float, ...]


def _label(verdict: dict[str, object]) -> str:
    error = str(verdict.get("error") or "")
    if error.startswith("llm_error"):
        return "loi_ha_tang"  # cổng LLM lỗi, mô hình chưa phán đoán (ví dụ HTTP 403)
    return str(verdict["label"])


def load(member: str, root: Path) -> tuple[list[Run], list[Alert]]:
    runs: list[Run] = []
    alerts: list[Alert] = []
    for path in sorted(root.glob("*-run/*/triage-result.json")):
        res = json.loads(path.read_text("utf-8"))["result"]
        run = res["run"]
        repo, pr = run["repo_alias"], int(run["pr_number"])
        llm = [v for v in res["verdicts"] if v["variant"] in VARIANTS]
        runs.append(
            Run(
                member, repo, pr, run["status"], run["manifest_hash"], float(run["duration_s"]),
                sum(int(v.get("tokens_in") or 0) + int(v.get("tokens_out") or 0) for v in llm),
                tuple(float(v["latency_ms"]) for v in llm if v.get("latency_ms")),
            )
        )  # fmt: skip
        by_id = {(v["finding_id"], v["variant"]): _label(v) for v in llm}
        for f in res["findings"]:
            labels = {var: by_id.get((f["finding_id"], var), "thieu") for var in VARIANTS}
            rule = f["rule_ids"][0].rsplit(".", 1)[-1]
            alerts.append(Alert(member, repo, pr, rule, f["file"].endswith(".java"), labels))
    return runs, alerts


def _table(head: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _pct(k: int, n: int) -> str:
    if not n:
        return "—"
    p = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.0f}%, KTC95 {100 * p.low:.0f}–{100 * p.high:.0f}%)"


def _q(values: Sequence[float], q: float) -> str:
    if not values:
        return "—"
    s = sorted(values)
    return f"{s[min(len(s) - 1, int(q * len(s)))]:.0f}"


def report(runs: list[Run], alerts: list[Alert], blind: bool) -> str:
    out: list[str] = ["# Tổng hợp số liệu A, B, C\n"]
    hashes = collections.Counter(r.manifest for r in runs)
    out.append("## 1. Kiểm tra nhất quán\n")
    out.append(
        _table(
            ["Thành viên", "Repo", "Lượt run", "ok / degraded / failed", "manifest_hash"],
            [
                (
                    m,
                    repo,
                    len(g),
                    "/".join(
                        str(sum(r.status == s for r in g)) for s in ("ok", "degraded", "failed")
                    ),
                    ", ".join(sorted({r.manifest for r in g})),
                )
                for (m, repo), g in _group(runs, lambda r: (r.member, r.repo))
            ],
        )  # fmt: skip
    )
    if len(hashes) == 1:
        out.append("\nMọi lượt dùng cùng một `manifest_hash`, gộp trực tiếp được.\n")
    else:
        out.append(
            f"\nCó **{len(hashes)}** `manifest_hash` khác nhau. Chỉ gộp trực tiếp các lượt cùng mã băm.\n"
        )

    out.append("## 2. Cách A: cảnh báo mới\n")
    out.append(
        _table(
            ["Thành viên", "Repo", "PR", "Cảnh báo mới", "Trong đó Java", "Cảnh báo/PR (trung vị)"],
            [
                (
                    m,
                    repo,
                    len({a.pr for a in g}),
                    len(g),
                    sum(a.java for a in g),
                    f"{statistics.median(collections.Counter(a.pr for a in g).values()):g}",
                )
                for (m, repo), g in _group(alerts, lambda a: (a.member, a.repo))
            ],
        )  # fmt: skip
    )
    out.append(
        f"\n**Tổng:** {len({(a.repo, a.pr) for a in alerts})} PR, {len(alerts)} cảnh báo mới, "
        f"{sum(a.java for a in alerts)} cảnh báo Java.\n"
    )
    by_rule = collections.Counter(a.rule for a in alerts)
    top = max(by_rule.values(), default=0)
    out.append(_table(["Luật", "Cảnh báo", "Số PR"], [
        (rule, n, len({(a.repo, a.pr) for a in alerts if a.rule == rule}))
        for rule, n in by_rule.most_common()
    ]))  # fmt: skip
    if alerts:
        out.append(f"\nLuật nhiều nhất chiếm {100 * top / len(alerts):.0f}% số cảnh báo.\n")

    out.append("## 3. Cách B và C: nhãn của LLM\n")
    if blind:
        out.append("Bỏ qua (`--mu`): không hiện nhãn B, C để giữ mù cho bước gán nhãn đáp án.\n")
    else:
        out.append(
            "Đây là đầu ra của LLM, **chưa phải đáp án**. Chưa tính được tỉ lệ loại sai hay loại nhầm.\n"
        )
        out.append(_table(["Nhãn", *VARIANTS], [
            (lab, *(sum(a.labels[v] == lab for a in alerts) for v in VARIANTS)) for lab in LABELS
        ]))  # fmt: skip
        n = len(alerts)
        decided = {v: sum(a.labels[v] in LABELS[:2] for a in alerts) for v in VARIANTS}
        dropped = {v: sum(a.labels[v] == "likely_false" for a in alerts) for v in VARIANTS}
        out.append("")
        out.append(_table(["Chỉ số", *VARIANTS], [
            ("Có kết luận (true hoặc false)", *(_pct(decided[v], n) for v in VARIANTS)),
            ("Bị ẩn khỏi comment (`likely_false`)", *(_pct(dropped[v], n) for v in VARIANTS)),
        ]))  # fmt: skip
        both = [a for a in alerts if all(a.labels[v] in LABELS[:2] for v in VARIANTS)]
        same = sum(a.labels["B"] == a.labels["C"] for a in both)
        out.append(
            f"\nB và C cùng có kết luận ở {len(both)} cảnh báo, trùng nhãn ở {same}. "
            f"Cặp lệch (B, C): {dict(collections.Counter((a.labels['B'], a.labels['C']) for a in alerts if a.labels['B'] != a.labels['C']))}.\n"
        )

    out.append("## 4. Vận hành\n")
    lat = [x for r in runs for x in r.latencies_ms]
    out.append(_table(["Chỉ số", "Trung vị", "p90", "Lớn nhất"], [
        ("Thời gian một lượt run (giây)", _q([r.duration_s for r in runs], 0.5),
         _q([r.duration_s for r in runs], 0.9), _q([r.duration_s for r in runs], 1.0)),
        ("Độ trễ một lần gọi LLM (ms)", _q(lat, 0.5), _q(lat, 0.9), _q(lat, 1.0)),
        ("Token B + C mỗi PR", _q([r.tokens for r in runs], 0.5),
         _q([r.tokens for r in runs], 0.9), _q([r.tokens for r in runs], 1.0)),
    ]))  # fmt: skip
    out.append(f"\nTổng token B + C: {sum(r.tokens for r in runs)}.\n")
    return "\n".join(out)


def _group[T](
    items: Iterable[T], key: Callable[[T], tuple[str, str]]
) -> list[tuple[tuple[str, str], list[T]]]:
    groups: dict[tuple[str, str], list[T]] = {}
    for it in items:
        groups.setdefault(key(it), []).append(it)
    return sorted(groups.items())


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("goi", nargs="+", help="<thanh-vien>=<thu-muc-goi-nop>")
    ap.add_argument("--mu", action="store_true", help="không hiện nhãn B, C")
    a = ap.parse_args(argv)
    runs: list[Run] = []
    alerts: list[Alert] = []
    for item in a.goi:
        member, _, folder = item.partition("=")
        if not folder:
            ap.error(f"cần dạng <thanh-vien>=<thu-muc>: {item}")
        r, al = load(member, Path(folder))
        if not r:
            ap.error(f"không thấy *-run/*/triage-result.json trong {folder}")
        runs += r
        alerts += al
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    print(report(runs, alerts, a.mu))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
