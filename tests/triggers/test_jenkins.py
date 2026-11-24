import json
from pathlib import Path

import pytest

from pr_triage.core.delivery import Channel, RepoAllowList, RepoGate, RoutePolicy
from pr_triage.core.scm import OpenPr
from pr_triage.triggers import (
    JenkinsParamsTrigger,
    JenkinsPoller,
    PollState,
    PollTrigger,
    TriggerError,
)


def gate(allow: str = "a/b, a/c", routes: str = "") -> RepoGate:
    return RepoGate(
        RepoAllowList.from_csv(allow, empty_allows_all=False), RoutePolicy.parse(routes)
    )


def pr(n: int, sha: str, base: str = "main", draft: bool = False) -> OpenPr:
    return OpenPr(n, sha, base, draft)


def test_params_parse_valid() -> None:
    reqs = JenkinsParamsTrigger().parse(
        {"REPO": "a/b", "PR": "7", "BASE_REF": "release/1.x", "HEAD_SHA": "abcdef1"}
    )
    assert len(reqs) == 1
    r = reqs[0]
    assert (r.repo, r.pr_number, r.base_ref, r.head_sha, r.channel) == (
        "a/b", 7, "release/1.x", "abcdef1", Channel.JENKINS,
    )  # fmt: skip


@pytest.mark.parametrize(
    "params",
    [
        {"REPO": "a b/c", "PR": "1"},
        {"REPO": "a/b", "PR": "x"},
        {"REPO": "a/b", "PR": "0"},
        {"REPO": "a/b", "PR": "1", "HEAD_SHA": "zz"},
        {"REPO": "a/b", "PR": "1", "BASE_REF": "--upload-pack=x"},
        {"REPO": "a/b", "PR": "1", "BASE_REF": "a/../b"},
        {"REPO": "a/b;rm", "PR": "1"},
        {},
    ],
)
def test_params_reject_injection_and_garbage(params: dict[str, str]) -> None:
    with pytest.raises(TriggerError):
        JenkinsParamsTrigger().parse(params)


def test_params_optional_fields_may_be_empty() -> None:
    r = JenkinsParamsTrigger().parse({"REPO": "a/b", "PR": "3", "BASE_REF": "", "HEAD_SHA": ""})[0]
    assert r.base_ref == "" and r.head_sha == ""


def test_collect_applies_gate_and_routes() -> None:
    trig, params = JenkinsParamsTrigger(), {"REPO": "a/b", "PR": "1"}
    assert len(trig.collect(params, gate())) == 1
    assert trig.collect({"REPO": "x/y", "PR": "1"}, gate()) == []
    assert trig.collect(params, gate(routes="github-app:a/b")) == []
    assert len(trig.collect(params, gate(routes="jenkins:a/*"))) == 1


def test_empty_allowlist_admits_nothing_for_jenkins() -> None:
    assert JenkinsParamsTrigger().collect({"REPO": "a/b", "PR": "1"}, gate(allow="")) == []


def test_poll_trigger_skips_seen_and_drafts() -> None:
    state = PollState({"a/b#1": "s1"})
    reqs = PollTrigger(state).parse(
        {"a/b": [pr(1, "s1"), pr(2, "s2", "dev"), pr(3, "s3", draft=True)]}
    )
    assert [(r.pr_number, r.head_sha, r.base_ref) for r in reqs] == [(2, "s2", "dev")]


def test_state_advance_drops_closed_keeps_failed_repo() -> None:
    state = PollState({"a/b#1": "s1", "a/b#9": "old", "a/c#5": "keep"})
    nxt = state.advance({"a/b": [pr(1, "s1b"), pr(3, "s3", draft=True)]}, frozenset({"a/c"}))
    assert nxt.as_dict() == {"a/b#1": "s1b", "a/c#5": "keep"}


def test_state_roundtrip_and_missing_file(tmp_path: Path) -> None:
    p = tmp_path / "s.json"
    assert PollState.load(p).as_dict() == {}
    PollState({"a/b#1": "x"}).save(p)
    assert json.loads(p.read_text()) == {"a/b#1": "x"}
    assert PollState.load(p).has_seen("a/b", 1, "x")


def test_poller_end_to_end_second_run_is_quiet() -> None:
    data = {"a/b": [pr(1, "s1"), pr(2, "s2")], "a/c": [pr(4, "s4", draft=True)]}
    poller = JenkinsPoller(lambda repo: data[repo], gate())
    first = poller.poll(PollState())
    assert sorted(r.pr_number for r in first.requests) == [1, 2] and first.asked == 2
    second = poller.poll(first.next_state)
    assert second.requests == []
    data["a/b"][0] = pr(1, "s1-new")
    third = poller.poll(second.next_state)
    assert [r.pr_number for r in third.requests] == [1]


def test_poller_one_failing_repo_keeps_old_state_and_continues() -> None:
    class Boom(Exception):
        code = 502

    def lister(repo: str) -> list[OpenPr]:
        if repo == "a/b":
            raise Boom
        return [pr(4, "s4")]

    poller = JenkinsPoller(lister, gate())
    out = poller.poll(PollState({"a/b#1": "old"}))
    assert out.failed == frozenset({"a/b"})
    assert [r.pr_number for r in out.requests] == [4]
    assert out.next_state.as_dict() == {"a/b#1": "old", "a/c#4": "s4"}
    assert poller.errors == ["a/b: không hỏi được GitHub (502)"]


def test_poller_ignores_wildcards_and_repos_routed_elsewhere() -> None:
    asked: list[str] = []

    def lister(repo: str) -> list[OpenPr]:
        asked.append(repo)
        return []

    g = gate(allow="a/*, a/b, a/c", routes="github-app:a/c, jenkins:a/b")
    JenkinsPoller(lister, g).poll(PollState())
    assert asked == ["a/b"]


def test_poller_handles_prefixed_hosts_without_clashing_with_github() -> None:
    data = {"a/b": [pr(1, "gh")], "gitlab:a/b": [pr(1, "gl")]}
    g = gate(allow="a/b, gitlab:a/b")
    out = JenkinsPoller(lambda repo: data[repo], g).poll(PollState())
    assert sorted((r.repo, r.head_sha) for r in out.requests) == [
        ("a/b", "gh"),
        ("gitlab:a/b", "gl"),
    ]


@pytest.mark.parametrize(
    "repo", ["gitlab:grp/sub/proj", "gitea:org/r", "bitbucket:PROJ/repo", "a/b"]
)
def test_params_accept_prefixed_and_nested_repos(repo: str) -> None:
    [req] = JenkinsParamsTrigger().parse({"REPO": repo, "PR": "2"})
    assert req.repo == repo


@pytest.mark.parametrize("repo", ["svn:a/b", "github:a/b", "gitlab:", "gitlab:solo", "a/b:c"])
def test_params_reject_unknown_prefix_or_shape(repo: str) -> None:
    with pytest.raises(TriggerError):
        JenkinsParamsTrigger().parse({"REPO": repo, "PR": "2"})
