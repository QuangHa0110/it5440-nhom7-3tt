from dataclasses import replace
from pathlib import Path

from pr_triage.bot import render
from pr_triage.core.models import Finding, RunMode, RunStatus, TriageResult, Variant
from pr_triage.core.ports import ContextPort
from pr_triage.pipeline import DisplayPolicy, PrPipeline
from pr_triage.pipeline.pathglob import any_match
from pr_triage.store import SqlStore
from tests.factories import make_finding
from tests.fakes import FakeContext, FakeLlm
from tests.helpers import git, make_repo
from tests.pipeline.test_runner import MarkerScanner


def findings() -> list[Finding]:
    return [
        replace(make_finding(ordinal=i), finding_id=f"f{i}", severity=sev, file=f"src/{i}.java")
        for i, sev in enumerate(["low", "high", "medium", "critical", "high"])
    ]


def test_select_orders_by_severity_and_applies_floor_and_cap() -> None:
    fs = findings()
    chosen, hidden = DisplayPolicy(min_severity="medium", max_findings=3).select(fs)
    assert [f.severity for f in chosen] == ["critical", "high", "high"] and hidden == 2
    chosen, hidden = DisplayPolicy().select(fs)
    assert len(chosen) == 5 and hidden == 0


def test_all_hidden_message_is_not_safe_claim() -> None:
    fs = findings()
    from pr_triage.core.models import PrRun

    run = PrRun(
        "r",
        "a",
        1,
        "h",
        "b",
        mode_comment(),
        RunStatus.OK,
        "t",
        notes=("ẩn: 5 cảnh báo dưới ngưỡng",),
    )
    body = render(TriageResult(run, tuple(fs)))
    assert (
        "không có cảnh báo nào đạt ngưỡng hiển thị" in body
        and "không có nghĩa là mã an toàn" in body
    )
    assert "5 cảnh báo dưới ngưỡng" in body


def mode_comment() -> RunMode:
    return RunMode.COMMENT


def test_pipeline_filter_and_hidden_note(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    git(repo, "switch", "-qc", "feature")
    for name in ("OrderDao", "OrderController"):
        p = repo / f"src/app/{name}.java"
        p.write_text(p.read_text().rstrip() + "\n// VULN\n")
    git(repo, "commit", "-qam", "thêm")
    ctx: dict[Variant, ContextPort] = {
        Variant.B: FakeContext(Variant.B),
        Variant.C: FakeContext(Variant.C),
    }

    def build(**kw: object) -> PrPipeline:
        return PrPipeline([MarkerScanner()], ctx, FakeLlm(), SqlStore(":memory:"), workers=1, **kw)  # type: ignore[arg-type]

    res = build().run(repo, "main", "feature", 1)
    assert len(res.findings) == 2
    only_dao = build(finding_filter=lambda f: not any_match(["**/OrderController.java"], f.file))
    res = only_dao.run(repo, "main", "feature", 1)
    assert [f.file for f in res.findings] == ["src/app/OrderDao.java"]
    capped = build(policy=DisplayPolicy(max_findings=1)).run(repo, "main", "feature", 1)
    assert len(capped.displayed) == 1 and any(n.startswith("ẩn: 1") for n in capped.run.notes)
    assert capped.run.status is RunStatus.OK
    assert "ẩn:" not in "".join(capped.errors)
    assert "1 cảnh báo dưới ngưỡng" in render(capped)
