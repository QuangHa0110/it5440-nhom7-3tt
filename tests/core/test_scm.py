import pytest

from pr_triage.core.errors import ScmError
from pr_triage.core.scm import GitRemote, ScmKind, join_repo, split_repo


def test_github_has_no_prefix() -> None:
    assert split_repo("acme/web") == (ScmKind.GITHUB, "acme/web")
    assert join_repo(ScmKind.GITHUB, "acme/web") == "acme/web"


@pytest.mark.parametrize(
    ("repo", "kind", "path"),
    [
        ("gitlab:grp/sub/proj", ScmKind.GITLAB, "grp/sub/proj"),
        ("gitea:org/repo", ScmKind.GITEA, "org/repo"),
        ("bitbucket:PROJ/repo", ScmKind.BITBUCKET, "PROJ/repo"),
    ],
)
def test_prefixed_repos_roundtrip(repo: str, kind: ScmKind, path: str) -> None:
    assert split_repo(repo) == (kind, path)
    assert join_repo(kind, path) == repo


@pytest.mark.parametrize("bad", ["svn:a/b", "gitlab:", "github:a/b"])
def test_bad_prefix_rejected(bad: str) -> None:
    with pytest.raises(ScmError):
        split_repo(bad)


def test_remote_refs_are_formatted() -> None:
    r = GitRemote("https://h/x.git", "u", ("refs/pull/{n}/head", "refs/pull/{n}/merge"))
    assert r.pr_refs(7) == ["refs/pull/7/head", "refs/pull/7/merge"]
