import shutil
import sys
from pathlib import Path

import pytest

from pr_triage.core.errors import ScanError
from pr_triage.scan import SemgrepAdapter
from tests.helpers import RULES, make_repo

pytestmark = pytest.mark.integration

if not (Path(sys.executable).parent / "semgrep").exists() and not shutil.which("semgrep"):
    pytest.skip("không có semgrep", allow_module_level=True)


def test_scan_sample_repo(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    found = SemgrepAdapter([str(RULES)]).scan(repo)
    by_rule = {(f.rule_id, f.file, f.line_start) for f in found}
    assert ("java-sqli-taint", "src/app/OrderController.java", 15) in by_rule
    assert ("java-sql-string-concat", "src/app/OrderDao.java", 10) in by_rule
    assert all(f.cwe == "CWE-89" and f.snippet for f in found)


def test_semgrep_ce_does_not_report_cross_function_taint(tmp_path: Path) -> None:
    """Ca thử T3: nguồn ở Controller.show, sink ở Dao.find. Semgrep CE không nối hai hàm."""
    repo = make_repo(tmp_path / "r")
    taint = [f for f in SemgrepAdapter([str(RULES)]).scan(repo) if f.rule_id == "java-sqli-taint"]
    assert [f.line_start for f in taint] == [15]


def test_timeout_raises(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    with pytest.raises(ScanError):
        SemgrepAdapter([str(RULES)], timeout_s=0).scan(repo)
