"""Phiếu gán nhãn mù (proposal 7.4). Mô-đun này cố ý không đọc bất kỳ kết quả nào của mô hình."""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

from pr_triage.core.models import HumanLabel, Label
from pr_triage.core.ports import StorePort

COLUMNS = [
    "finding_id", "cwe", "file", "line_start", "line_end", "tool_message", "code",
    "label", "reason", "code_ref", "is_test_code", "minutes",
]  # fmt: skip
DEV_DOUBLE = 30


class SheetError(ValueError):
    pass


def assign(
    ids: list[str], labelers: list[str], split: str, dev_double: int = DEV_DOUBLE
) -> dict[str, list[str]]:
    """Eval: hai người mỗi cảnh báo. Dev: hai người cho 30 ca đầu, còn lại một người."""
    if len(labelers) < 2:
        raise SheetError("cần ít nhất hai người gán nhãn")
    out: dict[str, list[str]] = defaultdict(list)
    n = len(labelers)
    for i, fid in enumerate(sorted(ids)):
        double = split == "eval" or i < dev_double
        out[fid].append(labelers[i % n])
        if double:
            out[fid].append(labelers[(i + 1) % n])
    return dict(out)


def export_sheets(
    store: StorePort, split: str, labelers: list[str], out_dir: Path, seed: int = 0
) -> dict[str, Path]:
    pool = [e for e in store.list_pool(split)]
    assignment = assign([e.finding_id for e in pool], labelers, split)
    per_labeler: dict[str, list[str]] = defaultdict(list)
    for fid, people in assignment.items():
        for p in people:
            per_labeler[p].append(fid)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for person, fids in per_labeler.items():
        rng = random.Random(f"{seed}:{person}")
        rng.shuffle(fids)
        path = out_dir / f"labels-{split}-{person}.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS)
            w.writeheader()
            for fid in fids:
                f = store.get_finding(fid)
                if f is None:
                    continue
                w.writerow({
                    "finding_id": f.finding_id, "cwe": f.cwe or "", "file": f.file,
                    "line_start": f.line_start, "line_end": f.line_end,
                    "tool_message": f.message, "code": f.snippet,
                })  # fmt: skip
        paths[person] = path
    return paths


def import_sheet(store: StorePort, labeler: str, path: Path) -> int:
    known = {e.finding_id for e in store.list_pool()}
    count = 0
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            value = (row.get("label") or "").strip().lower()
            if not value:
                continue
            fid = row["finding_id"]
            if fid not in known:
                raise SheetError(f"cảnh báo không có trong tập: {fid}")
            try:
                human = HumanLabel(value)
            except ValueError as exc:
                raise SheetError(f"{fid}: nhãn không hợp lệ {value!r}") from exc
            reason = (row.get("reason") or "").strip()
            if human is not HumanLabel.UNDETERMINED and not reason:
                raise SheetError(f"{fid}: nhãn {value} phải kèm một câu lý do")
            store.save_label(
                Label(
                    fid, labeler, human, reason, (row.get("code_ref") or "").strip(),
                    (row.get("is_test_code") or "").strip().lower() in ("1", "true", "yes", "x"),
                    int((row.get("minutes") or "0").strip() or 0),
                )
            )  # fmt: skip
            count += 1
    return count
