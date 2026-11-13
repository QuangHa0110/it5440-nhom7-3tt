from pathlib import Path

from pr_triage.context import SymbolIndex
from pr_triage.core.models import RawFinding
from pr_triage.normalize import deduplicate, new_findings, to_findings
from tests.helpers import FIXTURE, git, make_repo


def raw(rule: str = "r1", line: int = 10, tool: str = "semgrep", sev: str = "medium") -> RawFinding:
    return RawFinding(
        tool,
        rule,
        "msg",
        sev,
        "src/app/OrderDao.java",
        line,
        line,
        "CWE-89",
        'stmt.executeQuery("SELECT * FROM orders WHERE " + filter)',
    )


def resolver() -> "SymbolIndex":
    return SymbolIndex(FIXTURE)


def test_fingerprints_assigned_with_symbol() -> None:
    idx = resolver()
    (f,) = to_findings([raw()], FIXTURE, idx.enclosing_symbol)
    assert f.symbol == "OrderDao.find" and not f.no_symbol and len(f.finding_id) == 12


def test_same_code_twice_gets_distinct_ordinals() -> None:
    idx = resolver()
    a, b = to_findings([raw(line=10), raw(line=11)], FIXTURE, idx.enclosing_symbol)
    assert a.fingerprint != b.fingerprint


def test_no_symbol_flag_and_window(tmp_path: Path) -> None:
    (tmp_path / "x.txt").write_text("a\nb\nc\nd\ne\n")
    r = RawFinding("t", "r", "m", "low", "x.txt", 3, 3, None, "c")
    (f,) = to_findings([r], tmp_path, lambda p, ln: None)
    assert f.no_symbol and f.symbol is None


def test_new_findings_stable_when_lines_added_above(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    dao = repo / "src/app/OrderDao.java"
    base_sha = git(repo, "rev-parse", "HEAD")
    original = dao.read_text()
    dao.write_text(
        original.replace("public class OrderDao {", "public class OrderDao {\n    // một dòng\n\n")
    )
    git(repo, "commit", "-qam", "thêm dòng phía trên")
    assert base_sha != git(repo, "rev-parse", "HEAD")
    base = to_findings([raw(line=10)], FIXTURE, SymbolIndex(FIXTURE).enclosing_symbol)
    head = to_findings([raw(line=13)], repo, SymbolIndex(repo).enclosing_symbol)
    assert new_findings(head, base) == []


def test_new_findings_detects_added_vulnerability() -> None:
    idx = resolver()
    base = to_findings([raw(line=10)], FIXTURE, idx.enclosing_symbol)
    other = RawFinding(
        "semgrep", "r2", "m", "high", "src/app/OrderController.java", 15, 15, "CWE-89", "x"
    )
    head = to_findings([raw(line=10), other], FIXTURE, idx.enclosing_symbol)
    assert [f.rule_ids for f in new_findings(head, base)] == [("r2",)]


def test_dedup_merges_overlapping_same_cwe_symbol() -> None:
    idx = resolver()
    fs = to_findings(
        [raw("r1", 10, "semgrep", "medium"), raw("sb1", 10, "spotbugs", "high")],
        FIXTURE,
        idx.enclosing_symbol,
    )
    (m,) = deduplicate(fs)
    assert (
        m.tools == ("semgrep", "spotbugs") and m.rule_ids == ("r1", "sb1") and m.severity == "high"
    )


def test_dedup_keeps_apart_different_symbols_or_no_cwe() -> None:
    idx = resolver()
    other = RawFinding(
        "semgrep", "r1", "m", "low", "src/app/OrderController.java", 15, 15, "CWE-89", "x"
    )
    nocwe = RawFinding("semgrep", "r9", "m", "low", "src/app/OrderDao.java", 10, 10, None, "y")
    fs = to_findings([raw(), other, nocwe], FIXTURE, idx.enclosing_symbol)
    assert len(deduplicate(fs)) == 3
