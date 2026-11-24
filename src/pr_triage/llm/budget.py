"""Trần ngân sách token cho mỗi PR và mỗi ngày (ADR 0008)."""

from __future__ import annotations

import datetime as dt
import threading


class BudgetGuard:
    def __init__(self, per_pr_tokens: int = 200_000, per_day_tokens: int = 2_000_000) -> None:
        self._per_pr = per_pr_tokens
        self._per_day = per_day_tokens
        self._pr_used = 0
        self._day: dict[str, int] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _today() -> str:
        return dt.datetime.now(dt.UTC).date().isoformat()

    def allowed(self) -> bool:
        return self._pr_used < self._per_pr and self._day.get(self._today(), 0) < self._per_day

    def record(self, tokens: int) -> None:
        with self._lock:
            self._pr_used += tokens
            today = self._today()
            self._day[today] = self._day.get(today, 0) + tokens

    @property
    def pr_used(self) -> int:
        return self._pr_used
