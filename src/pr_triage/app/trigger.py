"""Đường GitHub App: sự kiện webhook thành `ScanRequest` (ADR 0018 D2)."""

from __future__ import annotations

from typing import Any

from pr_triage.app.webhook import parse_event
from pr_triage.core.delivery import Channel, ScanRequest
from pr_triage.core.models import JobKind
from pr_triage.triggers.base import Trigger

WebhookSource = tuple[str, dict[str, Any]]


class GitHubWebhookTrigger(Trigger[WebhookSource]):
    """Nguồn là (tên sự kiện, nội dung). Chỉ sự kiện cần quét (triage) mới thành yêu cầu.

    Sự kiện phản hồi và đóng PR không phải yêu cầu quét; server vẫn cho chúng qua cùng cổng repo.
    """

    def __init__(self, bot_login: str = "") -> None:
        self._bot = bot_login

    @property
    def channel(self) -> Channel:
        return Channel.GITHUB_APP

    def parse(self, source: WebhookSource) -> list[ScanRequest]:
        name, payload = source
        event = parse_event(name, payload, self._bot)
        if event is None or event.kind is not JobKind.TRIAGE:
            return []
        return [ScanRequest(event.repo, event.pr_number, event.key, self.channel, "", event.draft)]
