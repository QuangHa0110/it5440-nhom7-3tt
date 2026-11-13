from pathlib import Path

import pytest

from pr_triage.core.errors import ScanError
from pr_triage.core.models import (
    ContextBundle,
    Finding,
    RawFinding,
    RunMode,
    RunStatus,
    ShownAs,
    Variant,
    Verdict,
    VerdictLabel,
)
from pr_triage.core.ports import ContextPort, LlmPort
from pr_triage.pipeline import DisplayPolicy, PrPipeline, result_io
from pr_triage.store import SqlStore
from tests.fakes import FakeContext, FakeLlm
from tests.helpers import git, make_repo


class MarkerScanner:
    """Báo một cảnh báo tại mỗi dòng có chú thích `// VULN`."""

    name = "marker"

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def scan(self, checkout: Path, paths: object = None) -> list[RawFinding]:
        if self.fail:
            raise ScanError("hỏng")
        out: list[RawFinding] = []
        for p in sorted(checkout.rglob("*.java")):
            for i, line in enumerate(p.read_text().splitlines(), 1):
                if "// VULN" in line:
                    rel = p.relative_to(checkout).as_posix()
                    out.append(
                        RawFinding(
                            "marker", "r.sqli", "m", "high", rel, i, i, "CWE-89", line.strip()
                        )
                    )
        return out


def add_vuln(repo: Path) -> None:
    dao = repo / "src/app/OrderDao.java"
    dao.write_text(
        dao.read_text().replace(
            '"SELECT * FROM orders WHERE id = 1"', '"SELECT * FROM orders WHERE id = " + 1 // VULN'
        )
    )
    git(repo, "commit", "-qam", "thêm lỗ hổng")


def pipeline(
    store: SqlStore, llm: LlmPort | None = None, scanner: MarkerScanner | None = None, **kw: object
) -> PrPipeline:
    contexts: dict[Variant, ContextPort] = {
        Variant.B: FakeContext(Variant.B),
        Variant.C: FakeContext(Variant.C),
    }
    return PrPipeline(
        [scanner or MarkerScanner()],
        contexts,
        llm or FakeLlm(),
        store,
        repo_alias="repo-1",
        workers=2,
        **kw,  # type: ignore[arg-type]
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = make_repo(tmp_path / "r")
    git(r, "switch", "-qc", "feature")
    return r


def test_new_vulnerability_goes_through_all_variants(repo: Path) -> None:
    add_vuln(repo)
    store = SqlStore(":memory:")
    llm = FakeLlm()
    res = pipeline(store, llm).run(repo, "main", "feature", 7)
    assert res.run.status is RunStatus.OK and len(res.findings) == 1
    assert sorted(v.variant.value for v in res.verdicts) == ["A", "B", "C"]
    assert llm.calls == 2
    assert len(res.displayed) == 1 and res.displayed[0].displayed_variant is Variant.B
    assert store.get_run(res.run.run_id) is not None
    assert len(store.list_verdicts(res.run.run_id)) == 3
    assert store.list_displayed(res.run.run_id)[0].short_code == res.findings[0].finding_id[:6]
    occ = store.list_occurrences(res.run.run_id)
    assert [o.is_new for o in occ if o.side.value == "head"] == [True]


def test_no_new_findings_when_base_already_has_it(repo: Path) -> None:
    git(repo, "switch", "-q", "main")
    add_vuln(repo)
    git(repo, "switch", "-qc", "f2")
    (repo / "README").write_text("x")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "đổi không liên quan")
    llm = FakeLlm()
    res = pipeline(SqlStore(":memory:"), llm).run(repo, "main", "f2", 1)
    assert res.findings == () and llm.calls == 0 and res.run.status is RunStatus.OK


def test_scan_failure_marks_run_failed(repo: Path) -> None:
    res = pipeline(SqlStore(":memory:"), scanner=MarkerScanner(fail=True)).run(
        repo, "main", "feature", 1
    )
    assert res.run.status is RunStatus.FAILED and res.errors


def test_llm_error_degrades_but_keeps_alert(repo: Path) -> None:
    add_vuln(repo)

    class Broken:
        def triage(self, f: Finding, b: ContextBundle) -> Verdict:
            return Verdict(
                "v", f.finding_id, b.variant, "m", "p", VerdictLabel.UNKNOWN, error="llm_error: x"
            )

    res = pipeline(SqlStore(":memory:"), Broken()).run(repo, "main", "feature", 1)
    assert res.run.status is RunStatus.DEGRADED and len(res.displayed) == 1
    assert res.displayed[0].shown_as is ShownAs.EXPANDED


def test_false_label_is_collapsed_unknown_never(repo: Path) -> None:
    add_vuln(repo)

    class Falsy:
        def triage(self, f: Finding, b: ContextBundle) -> Verdict:
            return Verdict("v", f.finding_id, b.variant, "m", "p", VerdictLabel.LIKELY_FALSE)

    res = pipeline(SqlStore(":memory:"), Falsy()).run(repo, "main", "feature", 1)
    assert res.displayed[0].shown_as is ShownAs.COLLAPSED
    res_c = pipeline(SqlStore(":memory:"), Falsy(), policy=DisplayPolicy(Variant.A)).run(
        repo, "main", "feature", 1
    )
    assert res_c.displayed[0].shown_as is ShownAs.EXPANDED


def test_context_error_falls_back_to_snippet(repo: Path) -> None:
    from pr_triage.core.errors import ContextError

    add_vuln(repo)

    class BadC:
        variant = Variant.C

        def extract(self, f: Finding, checkout: Path) -> ContextBundle:
            raise ContextError("hỏng")

    store = SqlStore(":memory:")
    p = pipeline(store)
    p.contexts[Variant.C] = BadC()
    res = p.run(repo, "main", "feature", 1)
    c = [v for v in res.verdicts if v.variant is Variant.C]
    assert len(c) == 1 and res.run.status is RunStatus.DEGRADED
    assert any("ngữ cảnh C lỗi" in n for n in res.run.notes)


def test_result_json_roundtrip_and_tamper(repo: Path, tmp_path: Path) -> None:
    add_vuln(repo)
    res = pipeline(SqlStore(":memory:")).run(repo, "main", "feature", 1)
    path = tmp_path / "out" / "triage-result.json"
    result_io.write(res, path)
    assert result_io.read(path) == res
    with pytest.raises(result_io.ResultFormatError):
        result_io.loads('{"schema_version": 99, "result": {}}')
    with pytest.raises(result_io.ResultFormatError):
        result_io.loads(path.read_text().replace('"run_id"', '"rid"'))
    with pytest.raises(result_io.ResultFormatError):
        result_io.loads("không phải json")


def test_modes_recorded(repo: Path) -> None:
    res = pipeline(SqlStore(":memory:"), mode=RunMode.REPLAY).run(repo, "main", "feature", 1)
    assert res.run.mode is RunMode.REPLAY


def test_run_id_unique_per_run(repo: Path) -> None:
    p = pipeline(SqlStore(":memory:"))
    assert (
        p.run(repo, "main", "feature", 1).run.run_id != p.run(repo, "main", "feature", 1).run.run_id
    )


def test_empty_base_treats_every_finding_as_new(repo: Path) -> None:
    add_vuln(repo)
    res = pipeline(SqlStore(":memory:")).run(repo, "none", "feature", 1)
    assert res.run.base_sha == "" and len(res.findings) == 1
