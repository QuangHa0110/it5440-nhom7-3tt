"""Ranh giới import (ADR 0004 D4), kiểm tra bằng ast."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "pr_triage"

ALLOWED_PREFIX = {
    "core": {"core"},
    "store": {"core", "store"},
    "scan": {"core", "scan"},
    "normalize": {"core", "normalize"},
    "context": {"core", "context"},
    "llm": {"core", "llm"},
    "evaluation": {"core", "evaluation", "store"},
    "bot": {"core", "bot", "store"},
    "pipeline": {
        "core",
        "store",
        "scan",
        "normalize",
        "context",
        "llm",
        "bot",
        "evaluation",
        "pipeline",
    },
}


def imported_packages(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text("utf-8"))):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("pr_triage.")
        ):
            found.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("pr_triage."):
                    found.add(alias.name.split(".")[1])
    return found


def test_package_boundaries() -> None:
    violations: list[str] = []
    for pkg, allowed in ALLOWED_PREFIX.items():
        for file in (SRC / pkg).rglob("*.py"):
            bad = imported_packages(file) - allowed
            if bad:
                violations.append(f"{file.relative_to(SRC)} import {sorted(bad)}")
    assert not violations, violations


def test_checker_detects_violation(tmp_path: Path) -> None:
    f = tmp_path / "x.py"
    f.write_text("from pr_triage.bot import x\n")
    assert imported_packages(f) == {"bot"}
