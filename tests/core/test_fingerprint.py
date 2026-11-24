from pr_triage.core.fingerprint import FP_VERSION, finding_id, fingerprint, normalize_snippet

BASE = ("java.sqli", "src/A.java", "A.f", 'q("x" + id)', 0)


def test_stable_across_formatting_and_comments() -> None:
    a = fingerprint(*BASE)
    b = fingerprint("java.sqli", "src/A.java", "A.f", 'q(  "x"\n   + id) // chú thích', 0)
    assert a == b


def test_ignores_line_numbers_by_construction() -> None:
    assert "line" not in fingerprint.__code__.co_varnames


def test_changes_when_code_or_rule_or_ordinal_changes() -> None:
    base = fingerprint(*BASE)
    assert fingerprint("java.sqli", "src/A.java", "A.f", 'q("y" + id)', 0) != base
    assert fingerprint("java.xss", "src/A.java", "A.f", 'q("x" + id)', 0) != base
    assert fingerprint("java.sqli", "src/A.java", "A.f", 'q("x" + id)', 1) != base


def test_path_separators_and_version() -> None:
    assert fingerprint("r", "src\\A.java", None, "x", 0) == fingerprint(
        "r", "src/A.java", None, "x", 0
    )
    assert fingerprint("r", "p", None, "x", 0, version=FP_VERSION + 1) != fingerprint(
        "r", "p", None, "x", 0
    )


def test_finding_id_is_12_hex() -> None:
    assert len(finding_id(fingerprint(*BASE))) == 12


def test_normalize_removes_block_comments() -> None:
    assert normalize_snippet("a /* x\ny */ b") == "a b"
    assert normalize_snippet("q( 1 +  2 )") == "q(1+2)"
