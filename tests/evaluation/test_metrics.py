import math
from collections.abc import Sequence

import pytest

from pr_triage.evaluation.metrics import (
    bootstrap_by_group,
    cohen_kappa,
    mcnemar_exact,
    reads_saved_per_tp_lost,
    wilson,
)


def test_wilson_known_values_and_empty() -> None:
    p = wilson(50, 100)
    assert p.value == 0.5 and p.n == 100
    assert 0.40 < p.low < 0.41 and 0.59 < p.high < 0.60
    assert math.isclose(wilson(150, 300).high - wilson(150, 300).low, 2 * 0.0556, abs_tol=0.004)
    e = wilson(0, 0)
    assert e.value is None and (e.low, e.high) == (0.0, 1.0)


def test_mcnemar_exact() -> None:
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(0, 10) < 0.01
    assert math.isclose(mcnemar_exact(2, 8), 0.109375, abs_tol=1e-6)


def test_kappa() -> None:
    a = ["t", "t", "f", "f", "t", "f"]
    assert cohen_kappa(a, a) == 1.0
    assert math.isclose(cohen_kappa(["t", "t", "f", "f"], ["t", "f", "t", "f"]), 0.0, abs_tol=1e-9)
    assert math.isclose(
        cohen_kappa(["t", "t", "f", "f", "t"], ["t", "t", "f", "t", "t"]), 0.5454545, abs_tol=1e-4
    )
    with pytest.raises(ValueError):
        cohen_kappa([], [])
    with pytest.raises(ValueError):
        cohen_kappa(["a"], ["a", "b"])


def test_reads_saved_matches_proposal_examples() -> None:
    assert math.isclose(reads_saved_per_tp_lost(0.90, 0.95, 0.05) or 0, 171, abs_tol=0.01)
    assert math.isclose(reads_saved_per_tp_lost(0.22, 0.95, 0.05) or 0, 5.36, abs_tol=0.01)
    assert reads_saved_per_tp_lost(0.5, 0.9, 0.0) is None


def test_bootstrap_by_group_is_seeded_and_ordered() -> None:
    items = [("pr1", 1), ("pr1", 1), ("pr2", 0), ("pr3", 1), ("pr4", 0)]

    def mean(xs: Sequence[tuple[str, int]]) -> float:
        return sum(v for _, v in xs) / len(xs)

    ci = bootstrap_by_group(items, lambda t: t[0], mean, rounds=300, seed=1)
    assert ci is not None and 0.0 <= ci[0] <= ci[1] <= 1.0
    assert ci == bootstrap_by_group(items, lambda t: t[0], mean, rounds=300, seed=1)
    assert bootstrap_by_group([], lambda t: "x", lambda xs: 0.0) is None
