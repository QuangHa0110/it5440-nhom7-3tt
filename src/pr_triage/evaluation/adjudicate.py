"""Kappa, hàng đợi phân xử và nhãn cuối (proposal 7.4)."""

from __future__ import annotations

from dataclasses import dataclass

from pr_triage.core.models import Adjudication, HumanLabel
from pr_triage.core.ports import StorePort
from pr_triage.evaluation.metrics import cohen_kappa

KAPPA_MIN = 0.6


class KappaTooLow(Exception):
    pass


@dataclass(frozen=True)
class KappaResult:
    kappa: float | None
    n: int


def _pairs(store: StorePort) -> dict[str, tuple[HumanLabel, HumanLabel]]:
    by: dict[str, list[HumanLabel]] = {}
    for lab in store.list_labels():
        by.setdefault(lab.finding_id, []).append(lab.value)
    return {k: (v[0], v[1]) for k, v in by.items() if len(v) >= 2}


def kappa(store: StorePort) -> KappaResult:
    pairs = _pairs(store)
    if not pairs:
        return KappaResult(None, 0)
    a = [p[0].value for p in pairs.values()]
    b = [p[1].value for p in pairs.values()]
    return KappaResult(cohen_kappa(a, b), len(pairs))


def queue(store: StorePort) -> list[str]:
    """Ca bất đồng hoặc có người ghi Không xác định, chưa được phân xử."""
    done = {a.finding_id for a in store.list_adjudications()}
    out = [
        fid
        for fid, (x, y) in _pairs(store).items()
        if fid not in done and (x != y or HumanLabel.UNDETERMINED in (x, y))
    ]
    return sorted(out)


def finalize_agreed(store: StorePort, kappa_min: float = KAPPA_MIN) -> int:
    """Chốt các ca hai người đồng ý. Dừng nếu kappa dưới ngưỡng (phải sửa tiêu chí trước)."""
    k = kappa(store)
    if k.kappa is not None and k.kappa < kappa_min:
        raise KappaTooLow(
            f"kappa {k.kappa:.2f} dưới {kappa_min}: sửa tiêu chí gán nhãn rồi gán tiếp"
        )
    done = {a.finding_id for a in store.list_adjudications()}
    n = 0
    for fid, (x, y) in _pairs(store).items():
        if fid not in done and x == y and x is not HumanLabel.UNDETERMINED:
            store.save_adjudication(Adjudication(fid, x, "agreement"))
            n += 1
    for lab in store.list_labels():  # ca chỉ một người gán (tập dev)
        if lab.finding_id not in done and lab.finding_id not in _pairs(store):
            if lab.value is not HumanLabel.UNDETERMINED:
                store.save_adjudication(Adjudication(lab.finding_id, lab.value, lab.labeler_alias))
                n += 1
    return n


def adjudicate(
    store: StorePort, finding_id: str, value: HumanLabel, who: str, verified_by_z: bool = False
) -> None:
    store.save_adjudication(Adjudication(finding_id, value, who, verified_by_z))
