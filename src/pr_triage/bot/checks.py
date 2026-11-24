"""Check run kết luận `neutral` kèm chú thích theo dòng (ADR 0012 D6). Không chặn merge."""

from __future__ import annotations

from pr_triage.bot.sanitize import clean, clean_inline_code
from pr_triage.core.models import CheckAnnotation, RunStatus, ShownAs, TriageResult, VerdictLabel

CHECK_NAME = "PR Triage"
MAX_ANNOTATIONS = 50


def build_check(result: TriageResult) -> tuple[str, str, list[CheckAnnotation]]:
    run = result.run
    if run.status is RunStatus.FAILED:
        return (
            "Chưa quét xong",
            "Bước quét gặp lỗi. Không có kết luận nào về độ an toàn của thay đổi.",
            [],
        )
    by_id = {f.finding_id: f for f in result.findings}
    verdicts = {(v.finding_id, v.variant): v for v in result.verdicts}
    shown = [
        d for d in result.displayed if d.shown_as is ShownAs.EXPANDED and d.finding_id in by_id
    ]
    ann: list[CheckAnnotation] = []
    for d in shown[:MAX_ANNOTATIONS]:
        f = by_id[d.finding_id]
        v = verdicts.get((d.finding_id, d.displayed_variant))
        text = clean(v.explanation) if v and v.explanation and v.error is None else clean(f.message)
        level = "warning" if f.severity in ("high", "critical") else "notice"
        if v is not None and v.label is VerdictLabel.UNKNOWN:
            text = "Chưa đủ thông tin để kết luận. " + text
        ann.append(
            CheckAnnotation(
                clean_inline_code(f.file), f.line_start, max(f.line_end, f.line_start), level,
                clean(f"{f.severity}: {f.message}", 120), f"{text} (mã {d.short_code})",
            )
        )  # fmt: skip
    hidden = len([d for d in result.displayed if d.shown_as is ShownAs.COLLAPSED])
    title = f"{len(shown)} cảnh báo cần xem" if result.displayed else "Không có cảnh báo mới"
    summary = (
        f"{len(shown)} cảnh báo hiển thị, {hidden} có thể là báo sai (thu gọn). "
        "Bot không chặn merge và không bao giờ kết luận thay đổi là an toàn."
    )
    return title, summary, ann
