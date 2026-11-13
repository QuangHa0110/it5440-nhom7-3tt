from pathlib import Path

from pr_triage.store import BlobStore


def test_same_content_one_file(tmp_path: Path) -> None:
    b = BlobStore(tmp_path)
    r1, r2 = b.put(b"abc"), b.put(b"abc")
    assert r1 == r2
    assert sum(1 for p in tmp_path.rglob("*") if p.is_file()) == 1
    assert b.get(r1) == b"abc"
    assert b.exists(r1) and not b.exists("0" * 64)
