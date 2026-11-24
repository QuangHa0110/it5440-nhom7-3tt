"""Xuất số liệu tổng hợp ẩn danh để người của Z duyệt (proposal 10)."""

from __future__ import annotations

import json
from collections.abc import Collection
from typing import Any

K_MIN = 5


class LeakError(Exception):
    pass


def _suppress_prop(d: dict[str, Any], k: int) -> dict[str, Any]:
    if d["n"] < k:
        return {"n": None, "k": None, "low": None, "high": None, "suppressed": True}
    return d


def export_summary(report: dict[str, Any], k: int = K_MIN) -> dict[str, Any]:
    """Chỉ giữ số đếm và tỉ lệ. Ô có mẫu số dưới k bị che. Không có id, tên file, tên luật."""
    out: dict[str, Any] = {
        "split": report["split"],
        "k_min": k,
        "rq1_false_positive_rate": _suppress_prop(report["rq1_false_positive_rate"], k),
        "variants": {},
    }
    for name, v in report["variants"].items():
        out["variants"][name] = {
            key: _suppress_prop(v[key], k)
            for key in ("fp_removed", "tp_lost", "unknown_rate", "correct")
        }
    if "mcnemar_b_vs_c" in report:
        m = report["mcnemar_b_vs_c"]
        out["mcnemar_b_vs_c"] = m if m["n"] >= k else {"suppressed": True}
    return out


def assert_clean(summary: dict[str, Any], forbidden: Collection[str]) -> None:
    text = json.dumps(summary, ensure_ascii=False).lower()
    leaked = [f for f in forbidden if f and f.lower() in text]
    if leaked:
        raise LeakError(f"số liệu xuất chứa {len(leaked)} giá trị không được phép công bố")
