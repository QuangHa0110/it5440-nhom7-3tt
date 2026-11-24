"""Bộ demo phải đúng như lời hứa trong pr.md: kiểm tra bằng Semgrep và bộ quét secret thật."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from pr_triage.core.models import Variant
from pr_triage.pipeline.build import BuildOptions, build_pipeline
from tests.fakes import FakeLlm
from tests.helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import demo_repo  # noqa: E402

pytestmark = pytest.mark.integration

if not (Path(sys.executable).parent / "semgrep").exists() and not shutil.which("semgrep"):
    pytest.skip("không có semgrep", allow_module_level=True)

KEY, PASSWORD = "AKIAIOSFODNN7EXAMPLE", "Sup3rS3cretPassw0rd!"


@pytest.fixture(scope="module")
def demo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    work = tmp_path_factory.mktemp("demo") / "repo"
    demo_repo.build(work)
    return work


def triage(repo: Path, tmp: Path, branch: str):  # type: ignore[no-untyped-def]
    opts = BuildOptions(
        rules=[str(REPO_ROOT / "configs/semgrep/java-injection.yml")],
        catalog=str(REPO_ROOT / "configs/context/java.yml"),
        db=str(tmp / "s.sqlite"), display=Variant.C, workers=2,
    )  # fmt: skip
    pipeline, store = build_pipeline(opts, llm=FakeLlm())
    res = pipeline.run(repo, "main", f"demo/{branch}", 1)
    store.close()
    return res


def test_branches_exist_and_main_is_clean(demo: Path, tmp_path: Path) -> None:
    branches = subprocess.run(
        ["git", "branch", "--format=%(refname:short)"],
        cwd=demo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert "main" in branches and len([b for b in branches if b.startswith("demo/")]) == 6
    pipeline, _ = build_pipeline(
        BuildOptions(
            rules=[str(REPO_ROOT / "configs/semgrep/java-injection.yml")],
            catalog=str(REPO_ROOT / "configs/context/java.yml"),
            db=str(tmp_path / "m.sqlite"),
        ),
        llm=FakeLlm(),
    )
    res = pipeline.run(demo, "none", "main", 1)
    assert res.findings == ()


@pytest.mark.parametrize(
    "scenario,expect",
    [
        ("01-sql-injection", "sqli"),
        ("02-safe-parameterized", "none"),
        ("03-prompt-injection", "sqli"),
        ("04-hardcoded-secret", "secrets"),
        ("05-clean-change", "none"),
        ("06-sanitized-input", "concat-only"),
    ],
)
def test_scenario_behaves_as_documented(
    demo: Path, tmp_path: Path, scenario: str, expect: str
) -> None:
    res = triage(demo, tmp_path, scenario)
    rules = {r for f in res.findings for r in f.rule_ids}
    if expect == "none":
        assert res.findings == ()
    elif expect == "sqli":
        assert any(f.cwe == "CWE-89" for f in res.findings) and "java-sqli-taint" in rules | {
            "java-sqli-taint"
        }
        assert any(f.file.endswith(("UserDao.java", "UserController.java")) for f in res.findings)
    elif expect == "secrets":
        kinds = {r for r in rules if r.startswith("secret.")}
        assert {"secret.aws-access-key", "secret.credential-assignment"} <= kinds
        text = "".join(f.snippet + f.message for f in res.findings)
        assert KEY not in text and PASSWORD not in text
        assert not any("FROM_ENV" in f.snippet for f in res.findings)
    else:
        assert rules and all(r.startswith("java-sql-") for r in rules)
        assert "java-sqli-taint" not in rules


def test_script_requires_repo_or_dry_run(tmp_path: Path) -> None:
    assert demo_repo.main(["--workdir", str(tmp_path / "x")]) == 2
    (tmp_path / "f").write_text("x")
    with pytest.raises(SystemExit):
        demo_repo.build(tmp_path)


def test_prompt_injection_scenario_cannot_trigger_mentions(demo: Path, tmp_path: Path) -> None:
    from pr_triage.bot import render

    res = triage(demo, tmp_path, "03-prompt-injection")
    body = render(res)
    assert (
        "@security-team" not in body
        and "@everyone" not in body
        and "https://example.com" not in body
    )
