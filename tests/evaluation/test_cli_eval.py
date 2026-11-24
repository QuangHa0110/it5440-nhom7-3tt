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


def test_cli_single_labeler_then_audit_sample(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "s.sqlite"
    s = SqlStore(db)
    add_run(s, "r", "repoA", "2026-11-10T00:00:00Z", [(f"f{i:02d}", {}) for i in range(12)])
    s.close()
    base = ["eval", "--db", str(db)]
    assert cli.main([*base, "pool", "--cutoff", "2026-11-05T00:00:00Z"]) == 0
    out = tmp_path / "sheets"
    assert cli.main([*base, "label-export", "--split", "eval",
                     "--labelers", "ai-claude", "--single", "--out", str(out)]) == 0  # fmt: skip
    sheet = out / "labels-eval-ai-claude.csv"
    fill(sheet, {f"f{i:02d}": "false" for i in range(12)})
    assert cli.main([*base, "label-import", "--labeler", "ai-claude",
                     "--file", str(sheet)]) == 0  # fmt: skip
    capsys.readouterr()
    assert cli.main([*base, "audit-sample", "--split", "eval",
                     "--primary", "ai-claude", "--auditor", "human-1", "--n", "5",
                     "--seed", "1", "--out", str(out)]) == 0  # fmt: skip
    got = json.loads(capsys.readouterr().out)
    rows = list(csv.DictReader(Path(got["sheet"]).open()))
    assert len(rows) == 5 and all(r["label"] == "" for r in rows)


@pytest.mark.parametrize("change", ["run_config", "external_rules"])
def test_freeze_covers_run_config_and_external_rules(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs/eval").mkdir(parents=True)
    ext = tmp_path / "outside" / "registry.yml"
    ext.parent.mkdir()
    ext.write_text("rules: [a]")
    run_yml = tmp_path / "configs/eval/run.yml"
    run_yml.write_text(f"snippet_radius: 40\ndisplay: C\nexternal_rules:\n  - {ext}\n")
    monkeypatch.setenv("PR_TRIAGE_LLM_MODEL", "m")
    db = tmp_path / "s.sqlite"
    SqlStore(db).close()

    def run(*argv: str) -> int:
        return cli.main(["eval", "--db", str(db), *argv])

    assert run("freeze") == 0
    manifest = json.loads((tmp_path / "configs/eval/manifest.json").read_text())
    assert "configs/eval/run.yml" in manifest["files"]
    assert str(ext) in manifest["extra"]["external_rules"]
    assert run("metrics", "--split", "eval", "--rounds", "5") == 0
    capsys.readouterr()
    if change == "run_config":
        run_yml.write_text(run_yml.read_text().replace("40", "10"))
    else:
        ext.write_text("rules: [b]")
    assert run("metrics", "--split", "eval") == 3
    assert "lệch manifest" in capsys.readouterr().err


def test_freeze_rejects_missing_external_rules(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs/eval").mkdir(parents=True)
    (tmp_path / "configs/eval/run.yml").write_text("external_rules:\n  - /khong/ton/tai.yml\n")
    db = tmp_path / "s.sqlite"
    SqlStore(db).close()
    assert cli.main(["eval", "--db", str(db), "freeze"]) == 3
    assert "không tìm thấy" in capsys.readouterr().err
