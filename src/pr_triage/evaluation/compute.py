"""Tính số đo RQ1 và RQ2 trên các cảnh báo đã có nhãn cuối (proposal 7.6)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from pr_triage.core.models import HumanLabel, Variant, Verdict, VerdictLabel
from pr_triage.core.ports import StorePort
from pr_triage.evaluation.metrics import (
    Proportion,
    bootstrap_by_group,
    mcnemar_exact,
    reads_saved_per_tp_lost,
    wilson,
)

BASE_RATES = (0.22, 0.76, 0.92)


@dataclass(frozen=True)
class Item:
    finding_id: str
    pr: str
    truth: HumanLabel
    verdicts: dict[Variant, Verdict]


def load_items(store: StorePort, split: str) -> list[Item]:
    truth = {a.finding_id: a.final_value for a in store.list_adjudications()}
    cache: dict[str, dict[tuple[str, Variant], Verdict]] = {}
    items: list[Item] = []
    for e in store.list_pool(split):
        if e.finding_id not in truth:
            continue
        by = cache.get(e.run_id)
        if by is None:
            by = {(v.finding_id, v.variant): v for v in store.list_verdicts(e.run_id)}
            cache[e.run_id] = by
        verdicts = {v: by[(e.finding_id, v)] for v in Variant if (e.finding_id, v) in by}
        items.append(Item(e.finding_id, e.run_id, truth[e.finding_id], verdicts))
    return items


def _correct(item: Item, v: Variant) -> bool:
    verdict = item.verdicts.get(v)
    if verdict is None:
        return False
    return (verdict.label is VerdictLabel.LIKELY_TRUE and item.truth is HumanLabel.TRUE) or (
        verdict.label is VerdictLabel.LIKELY_FALSE and item.truth is HumanLabel.FALSE
    )


def _rates(items: Sequence[Item], v: Variant) -> tuple[Proportion, Proportion]:
    fp = [i for i in items if i.truth is HumanLabel.FALSE and v in i.verdicts]
    tp = [i for i in items if i.truth is HumanLabel.TRUE and v in i.verdicts]
    removed = sum(i.verdicts[v].label is VerdictLabel.LIKELY_FALSE for i in fp)
    lost = sum(i.verdicts[v].label is VerdictLabel.LIKELY_FALSE for i in tp)
    return wilson(removed, len(fp)), wilson(lost, len(tp))


def _variant_report(
    items: Sequence[Item], v: Variant, base_fp: float | None, rounds: int
) -> dict[str, Any]:
    fp_removed, tp_lost = _rates(items, v)
    judged = [i for i in items if v in i.verdicts]
    labels = [i.verdicts[v].label for i in judged]
    rates = list(BASE_RATES) + ([base_fp] if base_fp is not None else [])
    saved = {
        f"{r:.2f}": reads_saved_per_tp_lost(r, fp_removed.value or 0.0, tp_lost.value or 0.0)
        for r in rates
    }
    ci = bootstrap_by_group(
        list(items), lambda i: i.pr, lambda xs: _rates(xs, v)[0].value, rounds=rounds
    )
    return {
        "n": len(judged),
        "fp_removed": asdict(fp_removed),
        "tp_lost": asdict(tp_lost),
        "fp_removed_bootstrap_by_pr": ci,
        "unknown_rate": asdict(wilson(sum(x is VerdictLabel.UNKNOWN for x in labels), len(labels))),
        "invalid_rate": asdict(wilson(sum(x is VerdictLabel.INVALID for x in labels), len(labels))),
        "reads_saved_per_tp_lost": saved,
        "correct": asdict(wilson(sum(_correct(i, v) for i in judged), len(judged))),
    }


def compute_report(store: StorePort, split: str, rounds: int = 1000) -> dict[str, Any]:
    items = load_items(store, split)
    decided = [i for i in items if i.truth is not HumanLabel.UNDETERMINED]
    n_false = sum(i.truth is HumanLabel.FALSE for i in decided)
    fp_rate = wilson(n_false, len(decided))
    report: dict[str, Any] = {
        "split": split,
        "n_labeled": len(items),
        "n_true": sum(i.truth is HumanLabel.TRUE for i in items),
        "n_false": n_false,
        "n_undetermined": sum(i.truth is HumanLabel.UNDETERMINED for i in items),
        "rq1_false_positive_rate": asdict(fp_rate),
        "variants": {
            v.value: _variant_report(decided, v, fp_rate.value, rounds)
            for v in Variant
            if any(v in i.verdicts for i in decided)
        },
    }
    if any(Variant.B in i.verdicts and Variant.C in i.verdicts for i in decided):
        both = [i for i in decided if Variant.B in i.verdicts and Variant.C in i.verdicts]
        only_b = sum(_correct(i, Variant.B) and not _correct(i, Variant.C) for i in both)
        only_c = sum(_correct(i, Variant.C) and not _correct(i, Variant.B) for i in both)
        report["mcnemar_b_vs_c"] = {"n": len(both), "only_b_correct": only_b, "only_c_correct": only_c,
                                    "p_value": mcnemar_exact(only_b, only_c)}  # fmt: skip
    return report


def to_markdown(report: dict[str, Any]) -> str:
    def p(d: dict[str, Any]) -> str:
        if not d["n"]:
            return "n/a"
        return f"{d['k']}/{d['n']} = {d['k'] / d['n']:.1%} [{d['low']:.1%}, {d['high']:.1%}]"

    lines = [
        f"Tập `{report['split']}`: {report['n_labeled']} cảnh báo có nhãn "
        f"({report['n_true']} thật, {report['n_false']} sai, {report['n_undetermined']} không xác định).",
        f"RQ1, tỉ lệ cảnh báo sai: {p(report['rq1_false_positive_rate'])}",
        "",
        "| Cách | Loại được cảnh báo sai | Loại nhầm lỗi thật | Không xác định | Đúng |",
        "|---|---|---|---|---|",
    ]
    for name, v in report["variants"].items():
        lines.append(
            f"| {name} | {p(v['fp_removed'])} | {p(v['tp_lost'])} | {p(v['unknown_rate'])} | {p(v['correct'])} |"
        )
    if "mcnemar_b_vs_c" in report:
        m = report["mcnemar_b_vs_c"]
        lines += ["", f"McNemar B so với C trên {m['n']} cảnh báo: chỉ B đúng {m['only_b_correct']}, "
                      f"chỉ C đúng {m['only_c_correct']}, p = {m['p_value']:.3f}"]  # fmt: skip
    return "\n".join(lines) + "\n"
