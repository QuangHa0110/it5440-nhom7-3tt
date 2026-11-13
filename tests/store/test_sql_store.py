from pathlib import Path

import pytest

from pr_triage.core.models import (
    AlertState,
    DisplayedAlert,
    FeedbackEvent,
    FeedbackKind,
    Occurrence,
    ShownAs,
    Side,
    Variant,
)
from pr_triage.store import SqlStore
from tests.factories import make_bundle, make_finding, make_run, make_verdict


@pytest.fixture(params=["memory", "file"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> SqlStore:
    return SqlStore(":memory:" if request.param == "memory" else tmp_path / "db" / "t.sqlite")


def test_run_finding_roundtrip(store: SqlStore) -> None:
    run, f = make_run(), make_finding()
    store.save_run(run)
    store.upsert_finding(f)
    assert store.get_run("r1") == run
    assert store.get_finding(f.finding_id) == f
    assert store.get_run("nope") is None


def test_occurrence_bundle_verdict_displayed_feedback(store: SqlStore) -> None:
    f = make_finding()
    occ = Occurrence("r1", f.finding_id, Side.HEAD, 42, 42, "semgrep", True)
    store.add_occurrence(occ)
    store.add_occurrence(occ)
    assert store.list_occurrences("r1") == [occ]

    b = make_bundle(f)
    store.save_bundle(b)
    assert store.get_bundle(b.bundle_hash) == b

    v = make_verdict(f)
    store.save_verdict("r1", v)
    store.save_verdict("r1", make_verdict(f, Variant.C))
    assert store.list_verdicts("r1")[0] == v and len(store.list_verdicts("r1")) == 2

    d = DisplayedAlert("r1", f.finding_id, ShownAs.EXPANDED, Variant.B, AlertState.SHOWN, "abc123")
    store.save_displayed(d)
    assert store.list_displayed("r1") == [d]

    ev = FeedbackEvent("r1", f.finding_id, FeedbackKind.REPLY_FP, "user-1", "t", "vì sao")
    store.add_feedback(ev)
    store.add_feedback(ev)
    assert store.list_feedback("r1") == [ev, ev]


def test_persists_across_reopen(tmp_path: Path) -> None:
    path = tmp_path / "t.sqlite"
    s1 = SqlStore(path)
    s1.save_run(make_run())
    s1.close()
    s2 = SqlStore(path)
    assert s2.get_run("r1") is not None
    s2.close()


def test_blobs_through_store(tmp_path: Path) -> None:
    s = SqlStore(tmp_path / "t.sqlite")
    ref = s.put_blob(b"noi dung")
    assert s.get_blob(ref) == b"noi dung"
