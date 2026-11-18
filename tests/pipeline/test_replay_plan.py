"""Chọn cặp base/head và số PR cho `pr-triage replay`."""

from pathlib import Path

import pytest

from pr_triage.pipeline.gitrepo import pr_number_from_message
from pr_triage.pipeline.replay import plan_replay
from tests.helpers import git


@pytest.mark.parametrize(
    ("msg", "expected"),
    [
        ("Merge pull request #123 from a/b\n\nmô tả", 123),
        ("Fix x (#45)", 45),
        ("Fix x (#45)\n\nthân có (#99)", 45),
        ("chore: bump", None),
        ("Revert #12 nhưng không phải tiêu đề PR", None),
    ],
)
def test_pr_number_from_message(msg: str, expected: int | None) -> None:
    assert pr_number_from_message(msg) == expected


def history(tmp_path: Path) -> dict[str, str]:
    """main: init → merge #7 (nhánh 3 commit) → squash (#8) → commit thẳng."""
    r = tmp_path / "r"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / "a.txt").write_text("0\n")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "init")
    git(r, "switch", "-qc", "f1")
    for i in range(3):
        (r / "a.txt").write_text(f"{i + 1}\n")
        git(r, "commit", "-qam", f"f1 bước {i + 1}")
    first = git(r, "rev-list", "--reverse", "main..f1").split()[0]
    git(r, "switch", "-q", "main")
    git(r, "merge", "-q", "--no-ff", "f1", "-m", "Merge pull request #7 from a/f1")
    merge = git(r, "rev-parse", "HEAD")
    (r / "b.txt").write_text("x\n")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "Fix x (#8)")
    squash = git(r, "rev-parse", "HEAD")
    (r / "c.txt").write_text("y\n")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "chore: bump")
    direct = git(r, "rev-parse", "HEAD")
    return {"repo": str(r), "first": first, "merge": merge, "squash": squash, "direct": direct}


def test_plan_merged_uses_real_pr_numbers(tmp_path: Path) -> None:
    h = history(tmp_path)
    items = plan_replay(Path(h["repo"]), "HEAD", 3, "merged")
    by = {it.sha: it for it in items}
    assert by[h["merge"]].pr_number == 7
    assert by[h["squash"]].pr_number == 8
    assert by[h["direct"]].pr_number < 0
    assert by[h["squash"]].base == h["merge"] and by[h["squash"]].head == h["squash"]
    assert by[h["merge"]].head == git(Path(h["repo"]), "rev-parse", "f1")
    assert all(it.skip_reason is None for it in items)


def test_plan_side_first_uses_first_pr_commit_and_skips_single_parent(tmp_path: Path) -> None:
    h = history(tmp_path)
    by = {it.sha: it for it in plan_replay(Path(h["repo"]), "HEAD", 3, "first")}
    assert by[h["merge"]].head == h["first"] and by[h["merge"]].skip_reason is None
    assert by[h["squash"]].skip_reason and by[h["direct"]].skip_reason


def test_direct_commit_numbers_do_not_collide(tmp_path: Path) -> None:
    h = history(tmp_path)
    nums = [it.pr_number for it in plan_replay(Path(h["repo"]), "HEAD", 4, "merged")]
    assert len(nums) == len(set(nums))
