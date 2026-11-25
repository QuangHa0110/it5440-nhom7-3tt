"""Script lọc PR hai tầng: tầng 1 không bỏ sót commit mà pipeline đầy đủ thấy có cảnh báo mới."""

import dataclasses
import json
import shutil
import sys
from pathlib import Path

import pytest

from pr_triage.core.models import RawFinding, RunMode
from pr_triage.pipeline.build import BuildOptions, build_pipeline
from tests.helpers import REPO_ROOT, RULES, git, make_repo

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import filter_prs as fp  # noqa: E402

HAS_SEMGREP = (Path(sys.executable).parent / "semgrep").exists() or bool(shutil.which("semgrep"))

SQLI = """
    public String byName(java.sql.Statement stmt, String name) throws Exception {
        return stmt.executeQuery("SELECT * FROM orders WHERE name = '" + name + "'").toString();
    }
}
"""


def test_numstat_lines_bo_qua_file_nhi_phan() -> None:
    assert fp.numstat_lines("3\t1\ta.java\n-\t-\tlogo.png\n10\t0\tb.java\n") == 14
    assert fp.numstat_lines("") == 0


def test_parse_name_status() -> None:
    raw = b"M\0src/A.java\0A\0src/b c.java\0D\0old.java\0"
    assert fp.parse_name_status(raw) == [
        ("M", "src/A.java"),
        ("A", "src/b c.java"),
        ("D", "old.java"),
    ]


def test_split_by_side_tach_commit_va_phia() -> None:
    raw = RawFinding("semgrep", "r", "m", "high", "3/h/src/a b/A.java", 4, 4)
    groups = fp.split_by_side([raw, dataclasses.replace(raw, file="3/b/src/a b/A.java")])
    assert [g.file for g in groups[(3, "h")]] == ["src/a b/A.java"]
    assert set(groups) == {(3, "h"), (3, "b")}


def _history(tmp_path: Path) -> Path:
    repo = make_repo(tmp_path / "r")
    dao = repo / "src/app/OrderDao.java"
    dao.write_text(dao.read_text().rstrip().removesuffix("}") + SQLI)
    git(repo, "commit", "-qam", "them truy van noi chuoi")  # có cảnh báo mới
    head = "public class OrderDao {"
    dao.write_text(dao.read_text().replace(head, "/** DAO */\n" + head))
    git(repo, "commit", "-qam", "chi them chu thich")  # sửa Java, không có cảnh báo mới
    # Sửa đúng dòng bị báo, số cảnh báo giữ nguyên nhưng đoạn mã đổi: pipeline coi là cảnh báo mới.
    dao.write_text(
        dao.read_text().replace(
            "SELECT * FROM orders WHERE name", "SELECT id FROM orders WHERE name"
        )
    )
    git(repo, "commit", "-qam", "doi cot truy van")
    (repo / "README.md").write_text("tai lieu\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-qm", "chi sua tai lieu")  # không sửa Java: không vào kế hoạch
    return repo


def test_plan_chi_lay_commit_sua_java(tmp_path: Path) -> None:
    repo = _history(tmp_path)
    cands = fp.plan(repo, "HEAD", 10, 1000)
    assert [git(repo, "log", "-1", "--format=%s", c.sha) for c in cands] == [
        "doi cot truy van",
        "chi them chu thich",
        "them truy van noi chuoi",
    ]
    # P4: commit sửa nhiều dòng Java hơn trần thì bỏ (chú thích: 1 dòng; đổi cột: 2; truy vấn: 4)
    assert [c.java_lines for c in fp.plan(repo, "HEAD", 10, 2)] == [2, 1]


def test_plan_so_voi_merge_base_nhu_pipeline(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r")
    fork = git(repo, "rev-parse", "HEAD")
    git(repo, "switch", "-qc", "feature")
    dao = repo / "src/app/OrderDao.java"
    dao.write_text(dao.read_text().rstrip().removesuffix("}") + SQLI)
    git(repo, "commit", "-qam", "them truy van noi chuoi")
    git(repo, "switch", "-q", "main")
    (repo / "src/app/Other.java").write_text("package app;\nclass Other {}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "commit khac tren main")
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge pull request #7 from x/feature", "feature")
    [c] = [c for c in fp.plan(repo, "HEAD", 10, 1000) if c.pr == 7]
    assert c.base == fork  # không phải cha thứ nhất: Other.java không thuộc PR
    assert c.java_lines == 4


@pytest.mark.integration
@pytest.mark.skipif(not HAS_SEMGREP, reason="không có semgrep")
def test_prefilter_khop_pipeline_day_du(tmp_path: Path) -> None:
    repo = _history(tmp_path)
    out = tmp_path / "loc"
    assert (
        fp.main(
            [
                "prefilter",
                "--repo",
                str(repo),
                "--scan-back",
                "10",
                "--rules",
                str(RULES),
                "--out",
                str(out),
            ]
        )
        == 0
    )
    rows = {r["sha"]: r for r in json.loads((out / "prefilter.json").read_text())}
    pipeline, store = build_pipeline(
        BuildOptions(
            rules=[str(RULES)],
            db=str(tmp_path / "s.sqlite"),
            mode=RunMode.REPLAY,
            variants=(),
            secrets=False,
        )
    )
    for c in fp.plan(repo, "HEAD", 10, 1000):
        full = pipeline.run(repo, c.base, c.head, c.pr).findings
        assert rows[c.sha]["finding_ids"] == [f.finding_id for f in full], c
    store.close()
    assert len((out / "candidates.txt").read_text().split()) == 2
