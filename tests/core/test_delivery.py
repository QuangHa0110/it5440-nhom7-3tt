import pytest

from pr_triage.core.delivery import (
    Channel,
    DeliveryConfigError,
    RepoAllowList,
    RepoGate,
    RoutePolicy,
    ScanRequest,
)


def test_allowlist_matching_is_case_insensitive_glob() -> None:
    al = RepoAllowList.from_csv("Acme/*, other/one")
    assert al.allows("acme/web") and al.allows("OTHER/ONE")
    assert not al.allows("other/two") and not al.allows("evil/acme")


def test_empty_allowlist_meaning_is_explicit() -> None:
    assert RepoAllowList.from_csv("", empty_allows_all=True).allows("a/b")
    assert not RepoAllowList.from_csv("  , ", empty_allows_all=False).allows("a/b")


def test_exact_names_excludes_wildcards() -> None:
    al = RepoAllowList.from_csv("a/b, c/*, d/e?, f/[g]")
    assert al.exact_names() == ("a/b",)


def test_routes_without_rules_permit_every_channel() -> None:
    p = RoutePolicy.parse("")
    assert all(p.permits(c, "a/b") for c in Channel)


def test_routes_assign_one_channel_per_repo_and_deny_unmatched() -> None:
    p = RoutePolicy.parse("jenkins:acme/legacy-*, github-app:acme/web-*")
    assert p.permits(Channel.JENKINS, "acme/legacy-1")
    assert not p.permits(Channel.GITHUB_APP, "acme/legacy-1")
    assert p.permits(Channel.GITHUB_APP, "ACME/Web-2")
    assert not p.permits(Channel.JENKINS, "acme/other")  # không khớp luật nào
    assert not p.permits(Channel.GITHUB_APP, "acme/other")


def test_overlapping_patterns_fail_closed_on_both_channels() -> None:
    p = RoutePolicy.parse("jenkins:acme/*, github-app:acme/web-*")
    assert not p.permits(Channel.JENKINS, "acme/web-1")
    assert not p.permits(Channel.GITHUB_APP, "acme/web-1")
    assert p.permits(Channel.JENKINS, "acme/api")


@pytest.mark.parametrize(
    "raw", ["acme/x", "jenkins:", "gitlab:acme/x", "jenkins:a/b,github-app:A/B"]
)
def test_bad_route_config_is_rejected(raw: str) -> None:
    with pytest.raises(DeliveryConfigError):
        RoutePolicy.parse(raw)


def test_same_pattern_same_channel_twice_is_fine() -> None:
    assert len(RoutePolicy.parse("jenkins:a/b,jenkins:a/b").rules) == 2


def test_gate_needs_both_allowlist_and_route() -> None:
    gate = RepoGate(RepoAllowList.from_csv("acme/*"), RoutePolicy.parse("jenkins:acme/*"))
    assert gate.admits(Channel.JENKINS, "acme/x")
    assert not gate.admits(Channel.GITHUB_APP, "acme/x")
    assert not gate.admits(Channel.JENKINS, "evil/x")


def test_scan_request_is_immutable() -> None:
    r = ScanRequest("a/b", 1, "abc", Channel.JENKINS)
    with pytest.raises(AttributeError):
        r.repo = "x/y"  # type: ignore[misc]
