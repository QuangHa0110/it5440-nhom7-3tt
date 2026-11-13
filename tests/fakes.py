"""Bộ giả hiện thực các cổng, dùng cho test (ADR 0004)."""

from collections.abc import Sequence
from pathlib import Path

from pr_triage.core.models import (
    ContextBundle,
    Finding,
    PrRef,
    RawFinding,
    Reaction,
    Reply,
    Variant,
    Verdict,
)
from tests.factories import make_bundle, make_verdict


class FakeScanner:
    name = "fake"

    def __init__(self, findings: list[RawFinding]) -> None:
        self.findings = findings
        self.calls = 0

    def scan(self, checkout: Path, paths: Sequence[str] | None = None) -> list[RawFinding]:
        self.calls += 1
        return list(self.findings)


class FakeContext:
    def __init__(self, variant: Variant = Variant.B) -> None:
        self.variant = variant

    def extract(self, finding: Finding, checkout: Path) -> ContextBundle:
        return make_bundle(finding, self.variant)


class FakeLlm:
    def __init__(self) -> None:
        self.calls = 0

    def triage(self, finding: Finding, bundle: ContextBundle) -> Verdict:
        self.calls += 1
        return make_verdict(finding, bundle.variant)


class FakeScm:
    def __init__(self) -> None:
        self.comments: dict[str, str] = {}
        self.replies: list[Reply] = []
        self.reactions: list[Reaction] = []
        self.commits: list[str] = []
        self.state = "open"
        self.checks: dict[str, tuple[str, str, list[object]]] = {}

    def upsert_comment(self, pr: PrRef, marker: str, body: str) -> str:
        self.comments[marker] = body
        return f"c-{marker}"

    def list_replies(self, pr: PrRef, comment_ref: str) -> list[Reply]:
        return list(self.replies)

    def list_reactions(self, pr: PrRef, comment_ref: str) -> list[Reaction]:
        return list(self.reactions)

    def list_commits(self, pr: PrRef) -> list[str]:
        return list(self.commits)

    def upsert_check(
        self, pr: PrRef, name: str, title: str, summary: str, annotations: Sequence[object]
    ) -> str:
        self.checks[name] = (title, summary, list(annotations))
        return f"check-{name}"

    def pr_state(self, pr: PrRef) -> str:
        return self.state
