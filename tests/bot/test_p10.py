import httpx

from pr_triage.bot import (
    CHECK_NAME,
    FeedbackCollector,
    Publisher,
    build_check,
    clean,
    clean_inline_code,
    compute_cc,
    render,
    resolve_states,
)
from pr_triage.bot.github import GitHubScm, role_of
from pr_triage.core.alias import Aliaser
from pr_triage.core.models import (
    AlertState,
    FeedbackEvent,
    FeedbackKind,
    PrRef,
    Reply,
    RunMode,
    RunStatus,
    ShownAs,
    TriageResult,
    VerdictLabel,
)
from pr_triage.store import SqlStore
from tests.bot.test_bot import result
from tests.fakes import FakeScm

PR = PrRef("o/r", 5, "headsha", "b", "alice")


def test_clean_neutralizes_mentions_html_links_and_refs() -> None:
    t = clean(
        "Ping @victim và @org/team! <script>x</script> "
        "xem https://evil.example/a [x](http://y) #123 &amp;"
    )
    assert "@\u200bvictim" in t and "@\u200borg/team" in t
    assert "<script>" not in t and "&lt;script&gt;" in t
    assert "https\u200b://" in t and "http\u200b://" in t and "](" not in t
    assert "#\u200b123" in t
    assert len(clean("x" * 5000)) <= 600
    assert clean("a\n\n  b\tc") == "a b c"
    assert clean_inline_code("src/`evil`.java") == "src/'evil'.java"


def test_render_neutralizes_model_output_and_paths() -> None:
    r = result()
    f = r.findings[0]
    v = r.verdicts[0]
    from dataclasses import replace

    r = replace(
        r,
        findings=(replace(f, file="src/`x`@a.java", message="msg <b>x</b> @spam"),),
        verdicts=(replace(v, explanation="Gọi @boss ngay <img src=x onerror=1> https://x.io"),),
    )
    body = render(r)
    assert "@boss" not in body and "<img" not in body and "<b>" not in body
    assert "@\u200bboss" in body and "`src/'x'@a.java:42`" in body and "https\u200b://" in body


def test_render_cc_line_only_when_given() -> None:
    assert "cc @" not in render(result())
    assert "cc @alice @sec" in render(result(), cc=["@alice", "@sec"])


def test_compute_cc_modes_floor_and_validation() -> None:
    r = result()
    owners = lambda files: ["@own1", "@org/own2", "not-a-handle"]  # noqa: E731
    assert compute_cc(r, ["none"], "high", "alice") == []
    assert compute_cc(r, [], "high", "alice") == []
    assert compute_cc(r, ["author"], "high", "alice") == ["@alice"]
    assert compute_cc(r, ["author", "codeowners", "list"], "high", "alice", ["@list1"], owners) == [
        "@alice", "@own1", "@org/own2", "@list1",
    ]  # fmt: skip
    assert compute_cc(r, ["author"], "critical", "alice") == []
    assert compute_cc(r, ["author"], "high", "bad name") == []
    assert (
        compute_cc(
            r, ["author", "list"], "high", "alice", ["@alice", "@bot[bot]"], exclude=["@Alice"]
        )
        == []
    )
    collapsed = result(VerdictLabel.LIKELY_FALSE, ShownAs.COLLAPSED)
    assert compute_cc(collapsed, ["author"], "low", "alice") == []
    many = compute_cc(r, ["list"], "low", users=[f"@u{i}" for i in range(30)])
    assert len(many) == 10


def test_resolve_states_trusted_roles() -> None:
    r = result()
    a = r.displayed[0]
    fid = a.finding_id

    def ev(role: str) -> FeedbackEvent:
        return FeedbackEvent("r1", fid, FeedbackKind.REPLY_FP, "u", "t", "", role)

    def state(events: list[FeedbackEvent], trusted: list[str] | None) -> AlertState:
        return resolve_states([a], events, trusted_roles=trusted)[0].state

    assert state([ev("author")], ["reviewer"]) is AlertState.RESPONDED
    assert state([ev("author")], ["author", "reviewer"]) is AlertState.MARKED_FALSE
    assert state([ev("author"), ev("reviewer")], ["reviewer"]) is AlertState.MARKED_FALSE
    assert state([ev("other")], ["reviewer"]) is AlertState.RESPONDED
    assert state([ev("")], None) is AlertState.MARKED_FALSE


def test_collector_records_role() -> None:
    r = result()
    code = r.displayed[0].short_code
    scm, store = FakeScm(), SqlStore(":memory:")
    scm.replies = [
        Reply("1", "alice", f"fp {code}", "t1", "author"),
        Reply("2", "bob", f"tp {code}", "t2", "reviewer"),
    ]
    fresh = FeedbackCollector(scm, store, Aliaser("s")).collect(r, PR, "c")
    assert {(e.kind.value, e.actor_role) for e in fresh if e.finding_id} == {
        ("reply_fp", "author"), ("reply_tp", "reviewer"),
    }  # fmt: skip


def test_role_of() -> None:
    assert role_of("Alice", "NONE", "alice") == "author"
    assert role_of("bob", "MEMBER", "alice") == "reviewer"
    assert role_of("bob", "COLLABORATOR", "alice") == "reviewer"
    assert role_of("eve", "CONTRIBUTOR", "alice") == "other"
    assert role_of("eve", "", "") == "other"


def test_build_check_is_neutral_data_with_annotations() -> None:
    title, summary, ann = build_check(result())
    assert "1 cảnh báo cần xem" in title and "không bao giờ kết luận" in summary
    assert len(ann) == 1 and ann[0].path == "src/OrderDao.java" and ann[0].level == "warning"
    assert ann[0].start_line == 42 and "mã " in ann[0].message
    t2, s2, a2 = build_check(TriageResult(result().run))
    assert "Không có cảnh báo mới" in t2 and a2 == []
    from dataclasses import replace

    failed = replace(result(), run=replace(result().run, status=RunStatus.FAILED))
    assert build_check(failed)[2] == [] and "Chưa quét xong" in build_check(failed)[0]
    collapsed = build_check(result(VerdictLabel.LIKELY_FALSE, ShownAs.COLLAPSED))
    assert collapsed[2] == []


def test_publisher_posts_check_and_cc_only_when_asked() -> None:
    scm, store = FakeScm(), SqlStore(":memory:")
    pub = Publisher(scm, store)
    pub.publish(result(), PR, post=True)
    assert scm.checks == {}
    pub.publish(result(), PR, post=True, cc=["@alice"], check=True)
    assert CHECK_NAME in scm.checks and "cc @alice" in next(iter(scm.comments.values()))
    scm2 = FakeScm()
    Publisher(scm2, store).publish(result(mode=RunMode.SHADOW), PR, post=True, check=True)
    assert scm2.checks == {} and scm2.comments == {}


class CheckApi:
    def __init__(self, existing: bool = False) -> None:
        self.calls: list[tuple[str, str, dict[str, object]]] = []
        self.existing = existing

    def __call__(self, req: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(req.content) if req.content else {}
        self.calls.append((req.method, req.url.path, body))
        if req.method == "GET":
            return httpx.Response(200, json={"check_runs": [{"id": 77}] if self.existing else []})
        return httpx.Response(201, json={"id": 77})


def annotations(n: int):  # type: ignore[no-untyped-def]
    from pr_triage.core.models import CheckAnnotation

    return [CheckAnnotation(f"f{i}.java", 1, 1, "warning", "t", "m") for i in range(n)]


def test_github_check_creates_then_chunks_annotations() -> None:
    api = CheckApi()
    scm = GitHubScm("tok", transport=httpx.MockTransport(api), backoff_s=0)
    cid = scm.upsert_check(PR, "PR Triage", "t", "s", annotations(120))
    assert cid == "77"
    methods = [(m, p.rsplit("/", 1)[-1]) for m, p, _ in api.calls]
    assert methods == [
        ("GET", "check-runs"),
        ("POST", "check-runs"),
        ("PATCH", "77"),
        ("PATCH", "77"),
    ]
    first = api.calls[1][2]
    assert first["conclusion"] == "neutral" and first["status"] == "completed"
    assert [len(c[2]["output"]["annotations"]) for c in api.calls[1:]] == [50, 50, 20]  # type: ignore[index]


def test_github_check_updates_existing() -> None:
    api = CheckApi(existing=True)
    GitHubScm("tok", transport=httpx.MockTransport(api), backoff_s=0).upsert_check(
        PR, "PR Triage", "t", "s", []
    )
    assert [m for m, _, _ in api.calls] == ["GET", "PATCH"]
