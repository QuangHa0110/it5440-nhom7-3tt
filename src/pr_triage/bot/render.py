"""Dựng comment một lần cho mỗi PR (kiến trúc mục 7.3, ADR 0010)."""

from __future__ import annotations

from collections.abc import Sequence

from pr_triage.bot.sanitize import clean, clean_inline_code
from pr_triage.core.models import (
    DisplayedAlert,
    Finding,
    RunStatus,
    ShownAs,
    TriageResult,
    Verdict,
    VerdictLabel,
)

MARKER = "<!-- pr-triage:v1 -->"
_SEV = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
_NEVER_SAFE = "Việc không có cảnh báo không có nghĩa là mã an toàn."


def _alert_block(f: Finding, v: Verdict | None, code: str) -> str:
    cwe = f" ({f.cwe})" if f.cwe else ""
    head = (
        f"**{_SEV.get(f.severity, f.severity)}**, {clean(f.message, 160)}{cwe} "
        f"`{clean_inline_code(f.file)}:{f.line_start}`"
    )
    lines = [head]
    if v is not None and v.explanation and v.error is None:
        lines.append(clean(v.explanation))
    if v is not None and v.label is VerdictLabel.UNKNOWN and v.missing_context:
        lines.append("Chưa đủ thông tin: " + clean("; ".join(v.missing_context)))
    lines.append(f"Mã `{code}`")
    return "\n".join(lines)


def render(result: TriageResult, cc: Sequence[str] = ()) -> str:
    run = result.run
    if run.status is RunStatus.FAILED:
        return "\n".join(
            [
                MARKER,
                "## Kiểm tra bảo mật: chưa quét xong",
                "",
                "Bước quét gặp lỗi nên chưa có kết quả cho PR này. " + _NEVER_SAFE,
            ]
        )
    by_id = {f.finding_id: f for f in result.findings}
    verdicts = {(v.finding_id, v.variant): v for v in result.verdicts}
    shown: list[DisplayedAlert] = [d for d in result.displayed if d.shown_as is ShownAs.EXPANDED]
    hidden: list[DisplayedAlert] = [d for d in result.displayed if d.shown_as is ShownAs.COLLAPSED]

    def block(d: DisplayedAlert) -> str:
        return _alert_block(
            by_id[d.finding_id], verdicts.get((d.finding_id, d.displayed_variant)), d.short_code
        )

    unknown = sum(
        1
        for d in shown
        if (v := verdicts.get((d.finding_id, d.displayed_variant)))
        and v.label is not VerdictLabel.LIKELY_TRUE
    )
    out = [MARKER]
    if not result.displayed and result.findings:
        out += [
            "## Kiểm tra bảo mật: không có cảnh báo nào đạt ngưỡng hiển thị",
            "",
            "Các cảnh báo còn lại nằm dưới ngưỡng hoặc vượt giới hạn cấu hình. " + _NEVER_SAFE,
        ]
    elif not result.displayed:
        out += [
            "## Kiểm tra bảo mật: không có cảnh báo mới",
            "",
            "Công cụ quét không báo cảnh báo mới nào trong thay đổi này. " + _NEVER_SAFE,
        ]
    else:
        title = f"## Kiểm tra bảo mật: {len(shown)} cảnh báo cần xem"
        if unknown:
            title += f", {unknown} chưa đủ thông tin"
        out += [title, ""]
        out += (
            ["\n\n".join(block(d) for d in shown)] if shown else ["Không có cảnh báo nào cần mở."]
        )
        if hidden:
            out += [
                "",
                f"<details><summary>{len(hidden)} cảnh báo khác có thể là báo sai (bấm để mở)"
                "</summary>",
                "",
            ]
            out += ["\n\n".join(block(d) for d in hidden), "", "</details>"]
        out += [
            "",
            "Phản hồi: trả lời comment với `fp <mã>` nếu cảnh báo sai, `tp <mã>` nếu đúng.",
            "Bot không chặn merge và không sửa mã. " + _NEVER_SAFE,
        ]
    if cc:
        out += ["", "cc " + " ".join(cc)]
    for note in run.notes:
        if note.startswith("ẩn:"):
            out += ["", f"_{note[3:].strip().capitalize()}._"]
    if run.status is RunStatus.DEGRADED:
        out += [
            "",
            f"_Một số bước chưa hoàn tất ({len(result.errors)} ghi chú)."
            " Cảnh báo gốc được giữ nguyên._",
        ]
    return "\n".join(out) + "\n"
