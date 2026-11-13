import json
import math
from pathlib import Path

import pytest

from pr_triage.core.models import Adjudication, HumanLabel, Variant, VerdictLabel
from pr_triage.evaluation import (
    FreezeMismatch,
    build_pool,
    check_manifest,
    compute_manifest,
    compute_report,
    to_markdown,
    write_manifest,
)
from pr_triage.evaluation.export import LeakError, assert_clean, export_summary
from pr_triage.store import SqlStore
from tests.evaluation.helpers import add_run

L = VerdictLabel


def db() -> SqlStore:
    """10 cảnh báo sai (S), 10 thật (T). B loại 8/10 S và 1/10 T. C loại 9/10 S và 0/10 T."""
    s = SqlStore(":memory:")
    spec = []
    for i in range(10):
        b = L.LIKELY_FALSE if i < 8 else L.LIKELY_TRUE
        c = L.LIKELY_FALSE if i < 9 else L.LIKELY_TRUE
        spec.append((f"s{i}", {Variant.A: L.LIKELY_TRUE, Variant.B: b, Variant.C: c}))
    for i in range(10):
        b = L.LIKELY_FALSE if i < 1 else L.LIKELY_TRUE
        spec.append((f"t{i}", {Variant.A: L.LIKELY_TRUE, Variant.B: b, Variant.C: L.LIKELY_TRUE}))
    add_run(s, "run1", "repo", "2026-11-10T00:00:00Z", spec)
    build_pool(s, "2026-11-05T00:00:00Z")
    for name, _ in spec:
        s.save_adjudication(
            Adjudication(name, HumanLabel.FALSE if name[0] == "s" else HumanLabel.TRUE, "x")
        )
    return s


def test_report_numbers() -> None:
    r = compute_report(db(), "eval", rounds=50)
    assert (r["n_true"], r["n_false"]) == (10, 10)
    assert r["rq1_false_positive_rate"]["k"] == 10 and r["rq1_false_positive_rate"]["n"] == 20
    v = r["variants"]
    assert (v["A"]["fp_removed"]["k"], v["A"]["tp_lost"]["k"]) == (0, 0)
    assert (v["B"]["fp_removed"]["k"], v["B"]["tp_lost"]["k"]) == (8, 1)
    assert (v["C"]["fp_removed"]["k"], v["C"]["tp_lost"]["k"]) == (9, 0)
    assert math.isclose(v["B"]["reads_saved_per_tp_lost"]["0.50"], 8 / 1, abs_tol=1e-9)
    assert v["C"]["reads_saved_per_tp_lost"]["0.50"] is None
    assert v["B"]["correct"]["k"] == 17 and v["C"]["correct"]["k"] == 19
    m = r["mcnemar_b_vs_c"]
    assert (m["only_b_correct"], m["only_c_correct"]) == (0, 2) and 0 < m["p_value"] <= 1
    assert "McNemar" in to_markdown(r) and "| C |" in to_markdown(r)


def test_undetermined_excluded_from_rates() -> None:
    s = db()
    s.save_adjudication(Adjudication("s0", HumanLabel.UNDETERMINED, "x"))
    r = compute_report(s, "eval", rounds=20)
    assert r["n_undetermined"] == 1 and r["rq1_false_positive_rate"]["n"] == 19


def test_freeze_blocks_changes(tmp_path: Path) -> None:
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts/a.txt").write_text("v1")
    roots = [tmp_path / "prompts"]
    m = compute_manifest(roots, {"model": "m1", "prompt_version": "v1"}, base=tmp_path)
    path = tmp_path / "manifest.json"
    write_manifest(m, path)
    check_manifest(
        path, compute_manifest(roots, {"model": "m1", "prompt_version": "v1"}, base=tmp_path)
    )
    (tmp_path / "prompts/a.txt").write_text("v2")
    with pytest.raises(FreezeMismatch, match="prompts/a.txt"):
        check_manifest(
            path, compute_manifest(roots, {"model": "m1", "prompt_version": "v1"}, base=tmp_path)
        )
    (tmp_path / "prompts/a.txt").write_text("v1")
    with pytest.raises(FreezeMismatch, match="mô hình"):
        check_manifest(
            path, compute_manifest(roots, {"model": "m2", "prompt_version": "v1"}, base=tmp_path)
        )
    with pytest.raises(FreezeMismatch, match="chưa có manifest"):
        check_manifest(tmp_path / "none.json", m)


def test_export_suppresses_small_cells_and_has_no_identifiers() -> None:
    r = compute_report(db(), "eval", rounds=20)
    s = export_summary(r, k=15)
    assert s["rq1_false_positive_rate"]["n"] == 20
    assert s["variants"]["B"]["fp_removed"]["suppressed"] is True
    text = json.dumps(s)
    assert "finding_id" not in text and "src/" not in text
    assert_clean(s, {"src/s0.java", "tên-công-ty"})
    with pytest.raises(LeakError):
        assert_clean(s, {"suppressed"})
