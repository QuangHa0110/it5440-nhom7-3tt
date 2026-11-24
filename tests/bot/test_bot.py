from dataclasses import replace

import pytest

from pr_triage.bot import MARKER, FeedbackCollector, Publisher, fix_status, render, resolve_states
from pr_triage.bot.states import FixStatus
from pr_triage.core.alias import Aliaser
from pr_triage.core.models import (
    AlertState,
    DisplayedAlert,
    FeedbackKind,
    PrRef,
    Reaction,
    Reply,
    RunMode,
    RunStatus,
    ShownAs,
    TriageResult,
    Variant,
    Verdict,
    VerdictLabel,
)
from pr_triage.store import SqlStore
from tests.factories import make_finding, make_run
from tests.fakes import FakeScm

PR = PrRef("o/r", 1)


def result(
    label: VerdictLabel = VerdictLabel.LIKELY_TRUE,
    shown: ShownAs = ShownAs.EXPANDED,
    status: RunStatus = RunStatus.OK,
    mode: RunMode = RunMode.COMMENT,
) -> TriageResult:
    f = make_finding()
    v = Verdict(
        "v",
        f.finding_id,
        Variant.B,
        "m",
        "p",
        label,
        explanation="Giải thích ngắn.",
        missing_context=("callers",),
    )
    d = DisplayedAlert("r1", f.finding_id, shown, Variant.B, short_code=f.finding_id[:6])
    return TriageResult(replace(make_run(), status=status, mode=mode), (f,), (v,), (d,))


def test_render_expanded_and_codes() -> None:
    r = result()
    body = render(r)
    assert body.startswith(MARKER) and "1 cảnh báo cần xem" in body
    assert f"`{r.findings[0].finding_id[:6]}`" in body and "fp <mã>" in body
    assert "src/OrderDao.java:42" in body and "không có nghĩa là mã an toàn" in body
    assert "<details>" not in body


def test_render_collapsed_in_details() -> None:
    body = render(result(VerdictLabel.LIKELY_FALSE, ShownAs.COLLAPSED))
    assert "<details>" in body and "báo sai" in body and "Không có cảnh báo nào cần mở." in body


def test_render_unknown_counts_and_missing() -> None:
    body = render(result(VerdictLabel.UNKNOWN))
    assert "chưa đủ thông tin" in body and "Chưa đủ thông tin: callers" in body


def test_render_failed_empty_degraded_never_says_safe() -> None:
    failed = render(replace(result(), run=replace(make_run(), status=RunStatus.FAILED)))
    assert "chưa quét xong" in failed and "không có nghĩa là mã an toàn" in failed
    empty = render(TriageResult(make_run()))
    assert "không có cảnh báo mới" in empty and "không có nghĩa là mã an toàn" in empty
    assert "chưa hoàn tất" in render(result(status=RunStatus.DEGRADED))


def test_publisher_posts_once_and_updates() -> None:
    scm, store = FakeScm(), SqlStore(":memory:")
    pub = Publisher(scm, store)
    ref = pub.publish(result(), PR, post=True)
    assert ref == f"c-{MARKER}" and len(scm.comments) == 1
    pub.publish(result(), PR, post=True)
    assert len(scm.comments) == 1
    assert store.get_comment("r1") is not None


@pytest.mark.parametrize("mode", [RunMode.SHADOW, RunMode.REPLAY])
def test_publisher_never_posts_in_shadow_or_replay(mode: RunMode) -> None:
    scm = FakeScm()
    assert Publisher(scm, SqlStore(":memory:")).publish(result(mode=mode), PR, post=True) is None
    assert scm.comments == {}


def test_publisher_dry_run_default() -> None:
    scm = FakeScm()
    assert Publisher(scm, SqlStore(":memory:")).publish(result(), PR) is None and scm.comments == {}


def test_feedback_parses_fp_tp_per_alert_and_is_idempotent() -> None:
    r = result()
    code = r.displayed[0].short_code
    scm, store = FakeScm(), SqlStore(":memory:")
    scm.replies = [
        Reply("1", "alice", f"fp {code} vì đã làm sạch\nbình luận khác", "t1"),
        Reply("2", "bob", f"TP {code}", "t2"),
        Reply("3", "carol", "fp ffffff không tồn tại", "t3"),
        Reply("4", "dave", "chỉ là bình luận", "t4"),
    ]
    scm.reactions = [Reaction("c", "alice", "+1", "t5")]
    scm.commits = [r.run.head_sha, "newsha"]
    scm.state = "merged"
    col = FeedbackCollector(scm, store, Aliaser("salt"))
    fresh = col.collect(r, PR, "c")
    kinds = sorted(e.kind.value for e in fresh)
    assert kinds == sorted(["reply_fp", "reply_tp", "reaction", "commit", "merge"])
    fp = next(e for e in fresh if e.kind is FeedbackKind.REPLY_FP)
    assert fp.finding_id == r.findings[0].finding_id and fp.value == "vì đã làm sạch"
    assert "alice" not in fp.actor_alias and fp.actor_alias.startswith("user-")
    assert col.collect(r, PR, "c") == []
    assert len(store.list_feedback("r1")) == 5


def test_states_follow_diagram() -> None:
    r = result()
    a = r.displayed[0]
    fid = a.finding_id
    from pr_triage.core.models import FeedbackEvent as E

    def st(events: list[E], fixed: set[str] = frozenset(), closed: bool = False) -> AlertState:  # type: ignore[assignment]
        return resolve_states([a], events, fixed, closed)[0].state

    assert st([]) is AlertState.SHOWN
    assert st([], closed=True) is AlertState.IGNORED
    assert st([E("r1", fid, FeedbackKind.REPLY_TP, "u", "t")]) is AlertState.RESPONDED
    assert st(
        [
            E("r1", fid, FeedbackKind.REPLY_TP, "u", "t"),
            E("r1", fid, FeedbackKind.REPLY_FP, "u", "t"),
        ]
    ) is (AlertState.MARKED_FALSE)
    assert st([E("r1", fid, FeedbackKind.REPLY_FP, "u", "t")], {fid}) is AlertState.FIXED


def test_fix_status_rules() -> None:
    changed = {("A.java", "A.f")}
    assert fix_status("fp1", "A.java", "A.f", {"fp1"}, changed, set()) is FixStatus.PRESENT
    assert fix_status("fp1", "A.java", "A.f", set(), changed, set()) is FixStatus.FIXED
    assert fix_status("fp1", "A.java", "A.g", set(), changed, set()) is FixStatus.VANISHED_NOT_FIXED
    assert (
        fix_status("fp1", "A.java", "A.f", set(), changed, {"A.java"})
        is FixStatus.VANISHED_NOT_FIXED
    )
