"""Dữ liệu giả cho test đánh giá."""

from dataclasses import replace

from pr_triage.core.models import (
    FeedbackEvent as _Unused,  # noqa: F401
)
from pr_triage.core.models import (
    Occurrence,
    PrRun,
    RunMode,
    RunStatus,
    Side,
    Variant,
    Verdict,
    VerdictLabel,
)
from pr_triage.store import SqlStore
from tests.factories import make_finding


def add_run(
    store: SqlStore,
    run_id: str,
    repo: str,
    started: str,
    findings: list[tuple[str, dict[Variant, VerdictLabel]]],
) -> None:
    store.save_run(PrRun(run_id, repo, 1, "h", "b", RunMode.REPLAY, RunStatus.OK, started))
    for ordinal, (name, labels) in enumerate(findings):
        f = replace(make_finding(path=f"src/{name}.java", ordinal=ordinal), finding_id=name)
        store.upsert_finding(f)
        store.add_occurrence(Occurrence(run_id, name, Side.HEAD, 1, 1, "t", True))
        for variant, label in labels.items():
            store.save_verdict(
                run_id, Verdict(f"{name}-{variant.value}", name, variant, "m", "p", label)
            )
