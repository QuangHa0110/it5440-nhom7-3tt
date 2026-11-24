import json
from pathlib import Path

from pr_triage.context import SnippetProvider
from pr_triage.core.models import Variant
from pr_triage.core.secrets import find_kinds, is_reference, mask
from pr_triage.normalize import to_findings
from pr_triage.scan import SecretScanner
from pr_triage.store import SqlStore
from tests.factories import make_finding

AWS = "AKIAABCDEFGHIJKLMNOP"
PWD = "hunter2hunter2"


def repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/Config.java").write_text(
        f'class C {{\n  String key = "{AWS}";\n  String password = "{PWD}";\n'
        '  String ok = System.getenv("DB_PASSWORD");\n  String t = "${DB_PASSWORD}";\n}\n'
    )
    (tmp_path / "src/blob.bin").write_bytes(b"\x00\x01" + AWS.encode())
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules/x.js").write_text(f'var k = "{AWS}"')
    (tmp_path / "src/big.txt").write_text("a" * 2_000_000 + AWS)
    return tmp_path


def test_scanner_finds_and_never_keeps_the_value(tmp_path: Path) -> None:
    found = SecretScanner().scan(repo(tmp_path))
    kinds = {(f.rule_id, f.line_start) for f in found}
    assert ("secret.aws-access-key", 2) in kinds and ("secret.credential-assignment", 3) in kinds
    assert all(f.cwe == "CWE-798" and f.severity == "high" for f in found)
    blob = json.dumps([f.__dict__ for f in found], default=str)
    assert AWS not in blob and PWD not in blob and "[REDACTED]" in blob
    assert {f.file for f in found} == {"src/Config.java"}


def test_references_are_not_secrets() -> None:
    assert is_reference("${DB_PASSWORD}") and is_reference('System.getenv("X")')
    assert find_kinds('password = "${DB_PASSWORD}"') == []
    assert find_kinds('password = "hunter2hunter2"') == ["credential-assignment"]


def test_mask_counts_and_keeps_structure() -> None:
    out, n = mask(f'a = "{AWS}"; password="{PWD}"; int x = 1;')
    assert n == 2 and "int x = 1;" in out and AWS not in out and PWD not in out


def test_findings_and_bundles_carry_no_secret(tmp_path: Path) -> None:
    root = repo(tmp_path)
    raws = SecretScanner().scan(root)
    findings = to_findings(raws, root, lambda p, ln: None)
    assert all(AWS not in f.snippet and PWD not in f.snippet for f in findings)
    f = make_finding(path="src/Config.java", line=2)
    b = SnippetProvider(radius=3).extract(f, root)
    assert all(AWS not in s.text and PWD not in s.text for s in b.slices) and b.variant is Variant.B
    store = SqlStore(":memory:")
    store.save_bundle(b)
    assert AWS not in json.dumps(store.get_bundle(b.bundle_hash), default=str)
