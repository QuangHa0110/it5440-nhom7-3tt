"""Lớp trừu tượng của một đường kích hoạt (ADR 0018 D2)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pr_triage.core.delivery import Channel, RepoGate, ScanRequest

Source = TypeVar("Source")


class TriggerError(ValueError):
    """Nguồn kích hoạt sai dạng (tham số thiếu, không hợp lệ)."""


class Trigger(ABC, Generic[Source]):  # noqa: UP046 - giữ Generic tường minh cho mypy strict
    """Biến một nguồn (webhook, tham số job, kết quả poll) thành các `ScanRequest`.

    Lớp con chỉ cài đặt `channel` và `parse`. Việc lọc qua cổng repo nằm ở đây, nên không đường
    nào bỏ qua được danh sách cho phép và định tuyến.
    """

    @property
    @abstractmethod
    def channel(self) -> Channel: ...

    @abstractmethod
    def parse(self, source: Source) -> list[ScanRequest]:
        """Phân tích nguồn. Trả danh sách rỗng nếu không có gì để quét."""

    def collect(self, source: Source, gate: RepoGate) -> list[ScanRequest]:
        return [r for r in self.parse(source) if gate.admits(self.channel, r.repo)]
