import csv
import json
from pathlib import Path

import pytest

from pr_triage import cli
from pr_triage.core.models import Variant, VerdictLabel
from pr_triage.store import SqlStore
from tests.evaluation.helpers import add_run

T, F = VerdictLabel.LIKELY_TRUE, VerdictLabel.LIKELY_FALSE


def fill(path: Path, truth: dict[str, str]) -> None:
    rows = list(csv.DictReader(path.open()))
    for r in rows:
        r["label"] = truth[r["finding_id"]]
        r["reason"] = "lý do"
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_full_flow_with_freeze_gate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs/semgrep").mkdir(parents=True)
    (tmp_path / "configs/semgrep/r.yml").write_text("rules: []")
    monkeypatch.setenv("PR_TRIAGE_LLM_MODEL", "m")
    monkeypatch.setenv("PUBLIC_REPO_BLOCKLIST", str(tmp_path / "none.txt"))
    db = tmp_path / "s.sqlite"
    s = SqlStore(db)

    def pick(v: str) -> VerdictLabel:
        return F if v == "false" else T

    truth = {f"f{i:02d}": ("true" if i % 2 else "false") for i in range(12)}
    add_run(
        s, "r1", "repo", "2026-11-10T00:00:00Z",
        [
            (k, {Variant.A: T, Variant.B: pick(v), Variant.C: pick(v)})
            for k, v in truth.items()
        ],
    )  # fmt: skip
    s.close()

    def run(*argv: str) -> int:
        return cli.main(["eval", "--db", str(db), *argv])

    assert run("pool", "--cutoff", "2026-11-05T00:00:00Z") == 0
    assert json.loads(capsys.readouterr().out)["eval"] == 12
    assert (
        run("label-export", "--split", "eval", "--labelers", "a,b", "--out", str(tmp_path / "L"))
        == 0
    )
    for who in ("a", "b"):
        sheet = tmp_path / "L" / f"labels-eval-{who}.csv"
        fill(sheet, truth)
        assert run("label-import", "--labeler", who, "--file", str(sheet)) == 0
    capsys.readouterr()
    assert run("kappa") == 0 and json.loads(capsys.readouterr().out)["kappa"] == 1.0
    assert run("finalize") == 0 and json.loads(capsys.readouterr().out)["finalized"] == 12

    assert run("metrics", "--split", "eval") == 3
    assert "chưa có manifest" in capsys.readouterr().err
    assert run("freeze") == 0
    assert run("metrics", "--split", "eval", "--markdown", "--rounds", "20") == 0
    assert "| B |" in capsys.readouterr().out
    (tmp_path / "configs/semgrep/r.yml").write_text("rules: [changed]")
    assert run("metrics", "--split", "eval") == 3
    assert "lệch manifest" in capsys.readouterr().err
    assert run("metrics", "--split", "dev", "--rounds", "20") == 0

    out = tmp_path / "summary.json"
    capsys.readouterr()
    assert run("export", "--split", "eval", "--out", str(out), "--k", "5") == 0
    text = out.read_text()
    assert "src/" not in text and "f01" not in text
