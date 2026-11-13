"""Khóa cấu hình trước khi chạy tập eval (proposal 7.3): manifest có băm, từ chối chạy khi lệch."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class FreezeMismatch(Exception):
    pass


def _files(roots: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for r in roots:
        out.extend(sorted(p for p in r.rglob("*") if p.is_file()) if r.is_dir() else [r])
    return sorted(set(out))


def compute_manifest(
    roots: Iterable[Path], extra: dict[str, Any], base: Path = Path(".")
) -> dict[str, Any]:
    files = {
        p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in _files(roots)
    }
    payload = json.dumps({"files": files, "extra": extra}, sort_keys=True, ensure_ascii=False)
    return {"hash": hashlib.sha256(payload.encode()).hexdigest(), "files": files, "extra": extra}


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", "utf-8"
    )


def check_manifest(path: Path, current: dict[str, Any]) -> None:
    if not path.exists():
        raise FreezeMismatch(f"chưa có manifest {path}: chạy `pr-triage eval freeze` trước")
    frozen = json.loads(path.read_text("utf-8"))
    if frozen["hash"] == current["hash"]:
        return
    changed = sorted(
        k
        for k in set(frozen["files"]) | set(current["files"])
        if frozen["files"].get(k) != current["files"].get(k)
    )
    if frozen.get("extra") != current.get("extra"):
        changed.append("extra (mô hình, phiên bản prompt hoặc ngưỡng)")
    raise FreezeMismatch("cấu hình lệch manifest đã khóa: " + ", ".join(changed))
