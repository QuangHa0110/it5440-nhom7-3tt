"""Đăng comment trên PR, thu phản hồi, chạy trong CI."""

from pr_triage.bot.checks import CHECK_NAME, build_check
from pr_triage.bot.feedback import FeedbackCollector
from pr_triage.bot.mentions import compute_cc
from pr_triage.bot.publisher import Publisher
from pr_triage.bot.render import MARKER, render
from pr_triage.bot.sanitize import clean, clean_inline_code
from pr_triage.bot.sinks import ConsoleSink, ResultSink, ScmSink, choose_sink
from pr_triage.bot.states import FixStatus, fix_status, resolve_states

__all__ = [
    "CHECK_NAME",
    "MARKER",
    "ConsoleSink",
    "FeedbackCollector",
    "FixStatus",
    "Publisher",
    "ResultSink",
    "ScmSink",
    "build_check",
    "choose_sink",
    "clean",
    "clean_inline_code",
    "compute_cc",
    "fix_status",
    "render",
    "resolve_states",
]
