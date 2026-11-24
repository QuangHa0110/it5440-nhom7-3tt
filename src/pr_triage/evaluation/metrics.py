"""Số đo thống kê của đề tài (proposal 7.6, 7.7), dùng scipy và statsmodels."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from scipy.stats import binomtest
from statsmodels.stats.proportion import proportion_confint


@dataclass(frozen=True)
class Proportion:
    k: int
    n: int
    low: float
    high: float

    @property
    def value(self) -> float | None:
        return self.k / self.n if self.n else None


def wilson(k: int, n: int, alpha: float = 0.05) -> Proportion:
    """Tỉ lệ kèm mẫu số và khoảng Wilson 95%."""
    if n == 0:
        return Proportion(0, 0, 0.0, 1.0)
    low, high = proportion_confint(k, n, alpha=alpha, method="wilson")
    return Proportion(k, n, float(low), float(high))


def mcnemar_exact(only_first_correct: int, only_second_correct: int) -> float:
    """Giá trị p của kiểm định McNemar chính xác (hai phía) trên các ca bất đồng."""
    n = only_first_correct + only_second_correct
    if n == 0:
        return 1.0
    return float(binomtest(min(only_first_correct, only_second_correct), n, 0.5).pvalue)


def cohen_kappa(a: Sequence[str], b: Sequence[str]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("hai dãy nhãn phải cùng độ dài và không rỗng")
    n = len(a)
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def reads_saved_per_tp_lost(base_fp_rate: float, fp_removed: float, tp_lost: float) -> float | None:
    """Lượt đọc tiết kiệm trên mỗi lỗi thật bị mất, tính trên 100 cảnh báo (proposal mục 2)."""
    saved = 100 * base_fp_rate * fp_removed
    lost = 100 * (1 - base_fp_rate) * tp_lost
    return None if lost == 0 else saved / lost


def bootstrap_by_group[T](
    items: Sequence[T],
    group_of: Callable[[T], str],
    statistic: Callable[[Sequence[T]], float | None],
    rounds: int = 1000,
    seed: int = 0,
) -> tuple[float, float] | None:
    """Khoảng bootstrap 95% theo nhóm (cảnh báo cùng PR không độc lập, proposal 7.7)."""
    groups: dict[str, list[T]] = {}
    for it in items:
        groups.setdefault(group_of(it), []).append(it)
    keys = sorted(groups)
    if not keys:
        return None
    rng = random.Random(seed)
    vals: list[float] = []
    for _ in range(rounds):
        sample = [it for k in (rng.choice(keys) for _ in keys) for it in groups[k]]
        v = statistic(sample)
        if v is not None:
            vals.append(v)
    if not vals:
        return None
    vals.sort()
    return vals[int(0.025 * (len(vals) - 1))], vals[int(0.975 * (len(vals) - 1))]
