import csv
import re
from pathlib import Path

import pytest

from pr_triage.core.models import HumanLabel, Variant, VerdictLabel
from pr_triage.evaluation import adjudicate as adj
from pr_triage.evaluation import blind, build_pool
from pr_triage.store import SqlStore
from tests.evaluation.helpers import add_run

T = VerdictLabel.LIKELY_TRUE


def populated() -> SqlStore:
    s = SqlStore(":memory:")
    add_run(
        s, "old", "repoA", "2026-11-01T00:00:00Z", [("f1", {Variant.B: T}), ("f2", {Variant.B: T})]
    )
    add_run(
        s, "new", "repoA", "2026-11-10T00:00:00Z", [("f3", {Variant.B: T}), ("f1", {Variant.B: T})]
    )
    add_run(s, "priv", "repoZ", "2026-11-01T00:00:00Z", [("f4", {Variant.B: T})])
    return s


def test_pool_splits_by_time_and_eval_only_repo_first_occurrence_wins() -> None:
    s = populated()
    entries = {e.finding_id: e for e in build_pool(s, "2026-11-05T00:00:00Z", {"repoZ"})}
    assert {k: v.split for k, v in entries.items()} == {
        "f1": "dev",
        "f2": "dev",
        "f3": "eval",
        "f4": "eval",
    }
    assert entries["f1"].run_id == "old"
    assert [e.finding_id for e in s.list_pool("eval")] == ["f3", "f4"]


def test_assignment_rules() -> None:
    ids = [f"f{i:03d}" for i in range(40)]
    ev = blind.assign(ids, ["a", "b", "c"], "eval")
    assert all(len(set(v)) == 2 for v in ev.values())
    dev = blind.assign(ids, ["a", "b"], "dev")
    assert (
        sum(len(v) == 2 for v in dev.values()) == 30
        and sum(len(v) == 1 for v in dev.values()) == 10
    )
    with pytest.raises(blind.SheetError):
        blind.assign(ids, ["a"], "eval")


def test_sheets_are_blind_and_shuffled(tmp_path: Path) -> None:
    s = SqlStore(":memory:")
    add_run(
        s,
        "r",
        "repoA",
        "2026-11-10T00:00:00Z",
        [(f"f{i:02d}", {Variant.B: T, Variant.C: T}) for i in range(12)],
    )
    build_pool(s, "2026-11-05T00:00:00Z")
    paths = blind.export_sheets(s, "eval", ["a", "b"], tmp_path, seed=1)
    text = "".join(p.read_text() for p in paths.values())
    assert "likely_" not in text and "verdict" not in text.lower()
    rows = {k: [r["finding_id"] for r in csv.DictReader(p.open())] for k, p in paths.items()}
    assert sorted(rows["a"]) == sorted(rows["b"]) and rows["a"] != rows["b"]
    again = blind.export_sheets(s, "eval", ["a", "b"], tmp_path / "x", seed=1)
    assert [r["finding_id"] for r in csv.DictReader(again["a"].open())] == rows["a"]


def test_labeling_module_never_reads_model_output() -> None:
    src = Path(blind.__file__).read_text().lower()
    code = re.sub(r'""".*?"""', "", src, flags=re.S)
    assert "verdict" not in code and "list_verdicts" not in code


def fill(path: Path, value: str, reason: str = "lý do") -> None:
    rows = list(csv.DictReader(path.open()))
    for r in rows:
        r["label"], r["reason"] = value, reason
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=blind.COLUMNS)
        w.writeheader()
        w.writerows(rows)


def test_import_validation(tmp_path: Path) -> None:
    s = SqlStore(":memory:")
    add_run(s, "r", "repoA", "2026-11-10T00:00:00Z", [("f1", {Variant.B: T})])
    build_pool(s, "2026-11-05T00:00:00Z")
    p = blind.export_sheets(s, "eval", ["a", "b"], tmp_path)["a"]
    fill(p, "maybe")
    with pytest.raises(blind.SheetError, match="không hợp lệ"):
        blind.import_sheet(s, "a", p)
    fill(p, "true", reason="")
    with pytest.raises(blind.SheetError, match="lý do"):
        blind.import_sheet(s, "a", p)
    fill(p, "undetermined", reason="")
    assert blind.import_sheet(s, "a", p) == 1
    rows = list(csv.DictReader(p.open()))
    rows[0]["finding_id"] = "lạ"
    rows[0]["label"] = "true"
    rows[0]["reason"] = "x"
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=blind.COLUMNS)
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(blind.SheetError, match="không có trong tập"):
        blind.import_sheet(s, "a", p)


def label_all(s: SqlStore, who: str, values: dict[str, HumanLabel]) -> None:
    from pr_triage.core.models import Label

    for fid, v in values.items():
        s.save_label(Label(fid, who, v, "r"))


def test_kappa_queue_finalize_and_gate() -> None:
    s = SqlStore(":memory:")
    add_run(s, "r", "repoA", "2026-11-10T00:00:00Z", [(f"f{i}", {Variant.B: T}) for i in range(10)])
    build_pool(s, "2026-11-05T00:00:00Z")
    T_, F_, U_ = HumanLabel.TRUE, HumanLabel.FALSE, HumanLabel.UNDETERMINED
    a = {f"f{i}": (T_ if i % 2 else F_) for i in range(10)}
    b = dict(a)
    b["f0"] = T_
    b["f1"] = U_
    label_all(s, "a", a)
    label_all(s, "b", b)
    k = adj.kappa(s)
    assert k.n == 10 and k.kappa is not None and k.kappa > 0.6
    assert adj.queue(s) == ["f0", "f1"]
    assert adj.finalize_agreed(s) == 8
    adj.adjudicate(s, "f0", F_, "thu", True)
    assert adj.queue(s) == ["f1"] or adj.queue(s) == []
    assert {x.finding_id for x in s.list_adjudications()} >= {"f0", "f2"}


def test_low_kappa_blocks_finalize() -> None:
    s = SqlStore(":memory:")
    add_run(s, "r", "repoA", "2026-11-10T00:00:00Z", [(f"f{i}", {Variant.B: T}) for i in range(8)])
    T_, F_ = HumanLabel.TRUE, HumanLabel.FALSE
    label_all(s, "a", {f"f{i}": T_ if i < 4 else F_ for i in range(8)})
    label_all(s, "b", {f"f{i}": F_ if i < 4 else T_ for i in range(8)})
    with pytest.raises(adj.KappaTooLow):
        adj.finalize_agreed(s)
