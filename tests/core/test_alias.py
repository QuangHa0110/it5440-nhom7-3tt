import pytest

from pr_triage.core.alias import Aliaser


def test_deterministic_and_salted() -> None:
    a, b = Aliaser("s1"), Aliaser("s2")
    assert a.alias("file", "x.java") == a.alias("file", "x.java")
    assert a.alias("file", "x.java") != b.alias("file", "x.java")
    assert a.alias("file", "x") != a.alias("user", "x")
    assert "x.java" not in a.alias("file", "x.java")


def test_empty_salt_rejected() -> None:
    with pytest.raises(ValueError):
        Aliaser("")
