"""Các đường kích hoạt: biến sự kiện bên ngoài thành `ScanRequest` (ADR 0018)."""

from pr_triage.triggers.base import Trigger, TriggerError
from pr_triage.triggers.jenkins import (
    GitHubPullLister,
    JenkinsParamsTrigger,
    JenkinsPoller,
    PollOutcome,
    PollState,
    PollTrigger,
)

__all__ = [
    "GitHubPullLister",
    "JenkinsParamsTrigger",
    "JenkinsPoller",
    "PollOutcome",
    "PollState",
    "PollTrigger",
    "Trigger",
    "TriggerError",
]
