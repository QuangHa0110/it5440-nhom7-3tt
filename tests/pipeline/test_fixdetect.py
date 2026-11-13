from pathlib import Path

from pr_triage.bot.states import FixStatus
from pr_triage.core.models import Variant
from pr_triage.core.ports import ContextPort
from pr_triage.pipeline import PrPipeline
from pr_triage.pipeline.diffinfo import changed_symbols
from pr_triage.pipeline.fixdetect import detect_fixed
from pr_triage.store import SqlStore
from tests.fakes import FakeContext, FakeLlm
from tests.helpers import git, make_repo
from tests.pipeline.test_runner import MarkerScanner, add_vuln


def make_pipeline() -> PrPipeline:
    ctx: dict[Variant, ContextPort] = {
        Variant.B: FakeContext(Variant.B),
        Variant.C: FakeContext(Variant.C),
    }
    return PrPipeline(
        [MarkerScanner()], ctx, FakeLlm(), SqlStore(":memory:"), repo_alias="t", workers=1
    )


def vuln_pr(tmp_path: Path) -> tuple[Path, PrPipeline]:
    repo = make_repo(tmp_path / "r")
    git(repo, "switch", "-qc", "feature")
    add_vuln(repo)
    return repo, make_pipeline()


def test_fixed_when_function_changed_and_marker_gone(tmp_path: Path) -> None:
    repo, p = vuln_pr(tmp_path)
    res = p.run(repo, "main", "feature", 1)
    dao = repo / "src/app/OrderDao.java"
    dao.write_text(dao.read_text().replace(" // VULN", ""))
    git(repo, "commit", "-qam", "sửa")
    status = detect_fixed(p, repo, res, "feature")
    assert list(status.values()) == [FixStatus.FIXED]


def test_present_when_untouched_and_not_fixed_when_file_deleted(tmp_path: Path) -> None:
    repo, p = vuln_pr(tmp_path)
    res = p.run(repo, "main", "feature", 1)
    (repo / "README").write_text("x")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "không liên quan")
    assert list(detect_fixed(p, repo, res, "feature").values()) == [FixStatus.PRESENT]
    git(repo, "rm", "-q", "src/app/OrderDao.java")
    git(repo, "commit", "-qm", "xóa file")
    assert list(detect_fixed(p, repo, res, "feature").values()) == [FixStatus.VANISHED_NOT_FIXED]


def test_changed_symbols_maps_lines_to_functions(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    old = git(repo, "rev-parse", "HEAD")
    dao = repo / "src/app/OrderDao.java"
    dao.write_text(dao.read_text().replace('"SELECT * FROM orders WHERE id = 1"', '"SELECT 1"'))
    git(repo, "commit", "-qam", "đổi")
    changed, removed = changed_symbols(repo, old, git(repo, "rev-parse", "HEAD"), repo)
    assert ("src/app/OrderDao.java", "OrderDao.safe") in changed and not removed
