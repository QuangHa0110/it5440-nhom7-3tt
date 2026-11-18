"""Bộ luật dạng registry (ADR 0015): id luật và dấu vân tay không phụ thuộc nơi đặt file luật.

File tải từ semgrep.dev là JSON một dòng, id có dấu chấm. Semgrep thêm đường dẫn thư mục chứa
file luật vào trước id; nếu không bỏ được tiền tố này thì dấu vân tay đổi theo máy (dev, Docker,
Jenkins) và đường dẫn nội bộ lọt vào comment. Luật ở đây do nhóm tự viết theo đúng định dạng đó,
không chép từ registry.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

from pr_triage.context import SymbolIndex
from pr_triage.normalize import deduplicate, to_findings
from pr_triage.scan import SemgrepAdapter
from pr_triage.scan.semgrep import _local_rule_ids
from tests.helpers import make_repo

CONCAT = "java.test.sqli.concat-query.concat-query"
JDBC = "java.test.sqli.jdbc-query.jdbc-query"
REGISTRY_LIKE = {
    "rules": [
        {
            "id": CONCAT,
            "languages": ["java"],
            "severity": "WARNING",
            "message": "SQL dựng bằng nối chuỗi",
            "metadata": {"cwe": ["CWE-89: Improper Neutralization"], "confidence": "HIGH"},
            "pattern": "$STMT.executeQuery($A + $B)",
        },
        {
            "id": JDBC,
            "languages": ["java"],
            "severity": "WARNING",
            "message": "Truy vấn JDBC không dùng tham số",
            "metadata": {"cwe": ["CWE-89: Improper Neutralization"], "confidence": "LOW"},
            "pattern": "$STMT.executeQuery(...)",
        },
    ]
}


def _write(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(REGISTRY_LIKE, ensure_ascii=False, separators=(",", ":")), "utf-8")
    return dest


def test_local_rule_ids_reads_json_registry_file(tmp_path: Path) -> None:
    f = _write(tmp_path / "semgrep-default.yml")
    assert set(_local_rule_ids([str(f)])) == {CONCAT, JDBC}


needs_semgrep = pytest.mark.skipif(
    not (Path(sys.executable).parent / "semgrep").exists() and not shutil.which("semgrep"),
    reason="không có semgrep",
)


@pytest.mark.integration
@needs_semgrep
def test_rule_id_and_fingerprint_do_not_depend_on_rules_location(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    idx = SymbolIndex(repo)
    seen = []
    for where in ("a/semgrep-default.yml", "b/very/deep/dir/semgrep-default.yml"):
        raws = SemgrepAdapter([str(_write(tmp_path / where))]).scan(repo)
        seen.append(
            sorted(
                (f.rule_ids[0], f.fingerprint)
                for f in to_findings(raws, repo, idx.enclosing_symbol)
            )
        )
    assert seen[0] == seen[1]
    assert {rid for rid, _ in seen[0]} == {CONCAT, JDBC}


@pytest.mark.integration
@needs_semgrep
def test_two_cwe89_rules_on_same_line_merge_into_one_alert(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    raws = SemgrepAdapter([str(_write(tmp_path / "semgrep-default.yml"))]).scan(repo)
    idx = SymbolIndex(repo)
    on_dao = [
        f for f in to_findings(raws, repo, idx.enclosing_symbol) if f.symbol == "OrderDao.find"
    ]
    assert len(on_dao) == 2
    (merged,) = deduplicate(on_dao)
    assert merged.rule_ids == (CONCAT, JDBC) and merged.cwe == "CWE-89"
