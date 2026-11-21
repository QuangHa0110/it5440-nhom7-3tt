import io

import pytest

from pr_triage.bot import MARKER, ConsoleSink, ResultSink, ScmSink, choose_sink
from pr_triage.core.models import PrRef, RunMode
from pr_triage.core.ports import ScmPort
from pr_triage.store import SqlStore
from tests.bot.test_bot import result
from tests.fakes import FakeScm

PR = PrRef("o/r", 1)


def test_sinks_share_one_interface() -> None:
    assert issubclass(ConsoleSink, ResultSink) and issubclass(ScmSink, ResultSink)
    with pytest.raises(TypeError):
        ResultSink()  # type: ignore[abstract]


def test_console_sink_prints_and_returns_none() -> None:
    out = io.StringIO()
    assert ConsoleSink(out).deliver(result(), PR) is None
    assert MARKER in out.getvalue()


def test_scm_sink_posts_in_comment_mode() -> None:
    scm = FakeScm()
    ref = ScmSink(scm, SqlStore(":memory:")).deliver(result(), PR)
    assert ref == f"c-{MARKER}" and len(scm.comments) == 1


def test_scm_sink_still_silent_in_shadow() -> None:
    scm = FakeScm()
    assert ScmSink(scm, SqlStore(":memory:")).deliver(result(mode=RunMode.SHADOW), PR) is None
    assert scm.comments == {}


def test_choose_sink_does_not_build_scm_for_dry_run() -> None:
    def boom() -> ScmPort:
        raise AssertionError("không được dựng SCM khi chạy thử")

    sink = choose_sink(False, boom, SqlStore(":memory:"), io.StringIO())
    assert isinstance(sink, ConsoleSink)


def test_choose_sink_builds_scm_when_posting() -> None:
    scm = FakeScm()
    sink = choose_sink(True, lambda: scm, SqlStore(":memory:"))
    assert isinstance(sink, ScmSink)
    sink.deliver(result(), PR)
    assert len(scm.comments) == 1
