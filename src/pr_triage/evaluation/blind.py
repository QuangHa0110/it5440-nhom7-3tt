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
    ids: list[str],
    labelers: list[str],
    split: str,
    dev_double: int = DEV_DOUBLE,
    single: bool = False,
) -> dict[str, list[str]]:
    """Eval: hai người mỗi cảnh báo. Dev: hai người cho 30 ca đầu, còn lại một người.

    `single=True`: một người gán toàn bộ (người gán chính), người khác kiểm định mẫu qua
    `export_audit_sheet`.
    """
    if single:
        if len(labelers) != 1:
            raise SheetError("chế độ một người gán cần đúng một tên")
        return {fid: [labelers[0]] for fid in sorted(ids)}
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
    store: StorePort,
    split: str,
    labelers: list[str],
    out_dir: Path,
    seed: int = 0,
    single: bool = False,
) -> dict[str, Path]:
    pool = [e for e in store.list_pool(split)]
    assignment = assign([e.finding_id for e in pool], labelers, split, single=single)
    per_labeler: dict[str, list[str]] = defaultdict(list)
    for fid, people in assignment.items():
        for p in people:
            per_labeler[p].append(fid)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for person, fids in per_labeler.items():
        rng = random.Random(f"{seed}:{person}")
        rng.shuffle(fids)
        paths[person] = _write_sheet(store, fids, out_dir / f"labels-{split}-{person}.csv")
    return paths


def _write_sheet(store: StorePort, fids: list[str], path: Path) -> Path:
    """Phiếu chỉ có cảnh báo và vị trí mã; các cột nhãn để trống."""
    path.parent.mkdir(parents=True, exist_ok=True)
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
    return path


def _allocate(sizes: dict[tuple[str, str], int], n: int) -> dict[tuple[str, str], int]:
    """Phân bổ n theo tỉ lệ cỡ tầng, mỗi tầng không rỗng ít nhất 1 (khi n đủ), dư lớn nhất trước."""
    keys = sorted(k for k, v in sizes.items() if v > 0)
    total = sum(sizes[k] for k in keys)
    n = min(n, total)
    if n < len(keys):
        keys = sorted(keys, key=lambda k: (-sizes[k], k))[:n]
        return {k: 1 for k in keys}
    out = {k: 1 for k in keys}
    rest = n - len(keys)
    weights = {k: sizes[k] - 1 for k in keys}
    wsum = sum(weights.values())
    if rest and wsum:
        exact = {k: rest * weights[k] / wsum for k in keys}
        for k in keys:
            out[k] += int(exact[k])
        left = n - sum(out.values())
        for k in sorted(keys, key=lambda k: (-(exact[k] - int(exact[k])), k))[:left]:
            out[k] += 1
    return out


def export_audit_sheet(
    store: StorePort, split: str, primary: str, auditor: str, n: int, out_dir: Path, seed: int
) -> Path:
    """Phiếu kiểm định: mẫu n cảnh báo phân tầng theo (CWE, nhãn của người gán chính).

    Phiếu không chứa nhãn, lý do hay vị trí căn cứ của người gán chính.
    """
    pool = {e.finding_id for e in store.list_pool(split)}
    primary_labels = {
        lab.finding_id: lab.value.value
        for lab in store.list_labels()
        if lab.labeler_alias == primary and lab.finding_id in pool
    }
    if not primary_labels:
        raise SheetError(f"{primary} chưa gán nhãn cảnh báo nào trong tập {split}")
    strata: dict[tuple[str, str], list[str]] = defaultdict(list)
    for fid, value in sorted(primary_labels.items()):
        f = store.get_finding(fid)
        strata[((f.cwe if f else None) or "", value)].append(fid)
    quota = _allocate({k: len(v) for k, v in strata.items()}, n)
    rng = random.Random(f"{seed}:audit:{auditor}")
    chosen: list[str] = []
    for key in sorted(quota):
        chosen.extend(rng.sample(strata[key], quota[key]))
    rng.shuffle(chosen)
    return _write_sheet(store, chosen, out_dir / f"labels-{split}-{auditor}.csv")


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
