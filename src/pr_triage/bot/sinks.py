"""Nơi nhận kết quả: in ra console hoặc đăng lên SCM (ADR 0018 D5).

Nơi gọi chọn sink một lần; không rải `if mode` trong job hay Jenkinsfile.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import TextIO

from pr_triage.bot.publisher import Publisher
from pr_triage.bot.render import render
from pr_triage.core.models import PrRef, TriageResult
from pr_triage.core.ports import ScmPort, StorePort


class ResultSink(ABC):
    @abstractmethod
    def deliver(
        self, result: TriageResult, pr: PrRef, cc: Sequence[str] = (), check: bool = False
    ) -> str | None:
        """Trả về mã comment nếu đã đăng lên SCM, `None` nếu chỉ in."""


class ConsoleSink(ResultSink):
    """Chạy thử và chế độ shadow: chỉ in comment, không gọi SCM, không cần token."""

    def __init__(self, out: TextIO | None = None) -> None:
        self._out = out

    def deliver(
        self, result: TriageResult, pr: PrRef, cc: Sequence[str] = (), check: bool = False
    ) -> str | None:
        print(render(result, cc), file=self._out)
        return None


class ScmSink(ResultSink):
    """Đăng thật qua `Publisher` (vẫn không đăng nếu lượt chạy không ở chế độ comment)."""

    def __init__(self, scm: ScmPort, store: StorePort) -> None:
        self._publisher = Publisher(scm, store)

    def deliver(
        self, result: TriageResult, pr: PrRef, cc: Sequence[str] = (), check: bool = False
    ) -> str | None:
        return self._publisher.publish(result, pr, post=True, cc=cc, check=check)


def choose_sink(
    post: bool, scm_factory: Callable[[], ScmPort], store: StorePort, out: TextIO | None = None
) -> ResultSink:
    """`scm_factory` chỉ được gọi khi cần đăng thật, nên chạy thử không đòi token."""
    return ScmSink(scm_factory(), store) if post else ConsoleSink(out)
