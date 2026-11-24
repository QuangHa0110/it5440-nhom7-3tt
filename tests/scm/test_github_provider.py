import pytest

from pr_triage.app.github_provider import GitHubProvider
from pr_triage.core.errors import ScmError
from pr_triage.core.models import JobKind
from pr_triage.core.scm import ScmKind
from pr_triage.scm.provider import hmac_hex
from tests.scm.helpers import FakeHost


def provider(host: FakeHost | None = None, static_token: str = "", bot: str = "") -> GitHubProvider:
    h = host or FakeHost()
    return GitHubProvider(
        api_url="https://gh.test",
        webhook_secret="sek",
        static_token=static_token,
        bot=bot,
        transport=h.transport,
    )


def test_static_token_and_missing_token() -> None:
    assert provider(static_token="T").token() == "T"
    assert provider(static_token="T").token(5) == "T"  # không có App thì dùng token tĩnh
    with pytest.raises(ScmError):
        provider().token()


def test_remote_strips_nothing_for_plain_repo() -> None:
    r = provider().remote("acme/web")
    assert (r.url, r.username, r.bearer, r.pr_refs(3)) == (
        "https://github.com/acme/web.git", "x-access-token", False, ["refs/pull/3/head"],
    )  # fmt: skip


def test_webhook_verification_and_parse() -> None:
    p = provider(bot="app[bot]")
    body = b'{"x":1}'
    assert p.verify_webhook({"x-hub-signature-256": f"sha256={hmac_hex('sek', body)}"}, body)
    assert not p.verify_webhook({"x-hub-signature-256": "sha256=00"}, body)
    payload = {
        "action": "opened", "installation": {"id": 9}, "repository": {"full_name": "o/r"},
        "sender": {"login": "a"}, "number": 3,
        "pull_request": {"number": 3, "head": {"sha": "s"}, "draft": False},
    }  # fmt: skip
    ev = p.parse_webhook({"x-github-event": "pull_request"}, payload)
    assert ev is not None and (ev.kind, ev.repo, ev.installation_id) == (JobKind.TRIAGE, "o/r", 9)
    assert p.kind is ScmKind.GITHUB and p.webhook_path == "/webhook"
    assert p.bot_login() == "app[bot]"


def test_open_prs_via_api() -> None:
    from tests.scm.helpers import ok

    host = FakeHost()
    host.on(
        "GET", r"/repos/o/r/pulls\?state=open&per_page=100&page=1",
        lambda *_: ok(
            [{"number": 2, "head": {"sha": "s"}, "base": {"ref": "main"}, "draft": True}]
        ),
    )  # fmt: skip
    prs = provider(host).open_prs("TOK", "o/r")
    assert [(p.number, p.head_sha, p.base_ref, p.draft) for p in prs] == [(2, "s", "main", True)]
