"""Mô hình miền. Dataclass bất biến, không phụ thuộc thư viện ngoài."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def severity_rank(severity: str) -> int:
    return SEVERITY_RANK.get(severity, 1)


class Variant(StrEnum):
    A = "A"
    B = "B"
    C = "C"


class VerdictLabel(StrEnum):
    LIKELY_TRUE = "likely_true"
    LIKELY_FALSE = "likely_false"
    UNKNOWN = "unknown"
    INVALID = "invalid"


class RunMode(StrEnum):
    REPLAY = "replay"
    SHADOW = "shadow"
    COMMENT = "comment"


class RunStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"


class Side(StrEnum):
    HEAD = "head"
    BASE = "base"


class ShownAs(StrEnum):
    EXPANDED = "expanded"
    COLLAPSED = "collapsed"


class AlertState(StrEnum):
    SHOWN = "shown"
    RESPONDED = "responded"
    FIXED = "fixed"
    MARKED_FALSE = "marked_false"
    IGNORED = "ignored"


class FeedbackKind(StrEnum):
    REPLY_FP = "reply_fp"
    REPLY_TP = "reply_tp"
    REACTION = "reaction"
    COMMIT = "commit"
    MERGE = "merge"
    CLOSE = "close"


class HumanLabel(StrEnum):
    TRUE = "true"
    FALSE = "false"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class FlowStep:
    file: str
    line: int
    message: str = ""


@dataclass(frozen=True)
class RawFinding:
    """Cảnh báo thô do một công cụ quét báo ra, trước khi chuẩn hóa."""

    tool: str
    rule_id: str
    message: str
    severity: str
    file: str
    line_start: int
    line_end: int
    cwe: str | None = None
    snippet: str = ""
    flow: tuple[FlowStep, ...] = ()


@dataclass(frozen=True)
class Finding:
    """Cảnh báo duy nhất theo dấu vân tay (đơn vị phân tích của RQ1 và RQ2)."""

    finding_id: str
    fingerprint: str
    fp_version: int
    tools: tuple[str, ...]
    rule_ids: tuple[str, ...]
    message: str
    severity: str
    file: str
    line_start: int
    line_end: int
    cwe: str | None = None
    symbol: str | None = None
    snippet: str = ""
    flow: tuple[FlowStep, ...] = ()
    no_symbol: bool = False


@dataclass(frozen=True)
class Occurrence:
    run_id: str
    finding_id: str
    side: Side
    line_start: int
    line_end: int
    tool: str
    is_new: bool


@dataclass(frozen=True)
class ContextSlice:
    file: str
    start: int
    end: int
    role: str
    text: str


@dataclass(frozen=True)
class ContextBundle:
    bundle_hash: str
    variant: Variant
    finding_id: str
    slices: tuple[ContextSlice, ...]
    source: str | None = None
    sink: str | None = None
    sanitizers: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    extract_ms: int = 0


@dataclass(frozen=True)
class EvidenceItem:
    file: str
    line: int
    note: str = ""


@dataclass(frozen=True)
class Verdict:
    verdict_id: str
    finding_id: str
    variant: Variant
    model_id: str
    prompt_version: str
    label: VerdictLabel
    explanation: str = ""
    evidence: tuple[EvidenceItem, ...] = ()
    missing_context: tuple[str, ...] = ()
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    cached: bool = False
    error: str | None = None


@dataclass(frozen=True)
class PrRun:
    run_id: str
    repo_alias: str
    pr_number: int
    head_sha: str
    base_sha: str
    mode: RunMode
    status: RunStatus
    started_at: str
    duration_s: float = 0.0
    manifest_hash: str = ""
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DisplayedAlert:
    run_id: str
    finding_id: str
    shown_as: ShownAs
    displayed_variant: Variant
    state: AlertState = AlertState.SHOWN
    short_code: str = ""


@dataclass(frozen=True)
class FeedbackEvent:
    run_id: str
    finding_id: str | None
    kind: FeedbackKind
    actor_alias: str
    at: str
    value: str = ""


@dataclass(frozen=True)
class Label:
    finding_id: str
    labeler_alias: str
    value: HumanLabel
    reason: str
    code_ref: str = ""
    is_test_code: bool = False
    minutes: int = 0


@dataclass(frozen=True)
class PoolEntry:
    finding_id: str
    split: str
    run_id: str
    repo_alias: str


@dataclass(frozen=True)
class Adjudication:
    finding_id: str
    final_value: HumanLabel
    adjudicator_alias: str
    verified_by_z: bool = False


@dataclass(frozen=True)
class Reply:
    comment_ref: str
    author: str
    body: str
    at: str


@dataclass(frozen=True)
class Reaction:
    comment_ref: str
    author: str
    content: str
    at: str


@dataclass(frozen=True)
class PostedComment:
    run_id: str
    comment_ref: str
    body_hash: str
    posted_at: str


@dataclass(frozen=True)
class PrRef:
    repo: str
    number: int
    head_sha: str = ""
    base_sha: str = ""


@dataclass(frozen=True)
class TriageResult:
    """Kết quả một lượt chạy, trao từ job triage sang job publish."""

    run: PrRun
    findings: tuple[Finding, ...] = ()
    verdicts: tuple[Verdict, ...] = ()
    displayed: tuple[DisplayedAlert, ...] = ()
    errors: tuple[str, ...] = field(default=())
