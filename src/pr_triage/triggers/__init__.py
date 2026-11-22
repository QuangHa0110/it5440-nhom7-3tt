"""Các đường kích hoạt: biến sự kiện bên ngoài thành `ScanRequest` (ADR 0018)."""

from pr_triage.triggers.base import Trigger, TriggerError
from pr_triage.triggers.jenkins import (
    JenkinsParamsTrigger,
    JenkinsPoller,
    PollOutcome,
    PollState,
    PollTrigger,
)

__all__ = [
    "JenkinsParamsTrigger",
    "JenkinsPoller",
    "PollOutcome",
    "PollState",
    "PollTrigger",
    "Trigger",
    "TriggerError",
]
