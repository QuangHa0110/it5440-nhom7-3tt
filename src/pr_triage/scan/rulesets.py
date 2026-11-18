"""Bộ luật Semgrep tải từ registry, khóa bằng mã băm (ADR 0015).

File luật không vào repo (giấy phép không cho phân phối lại). Repo chỉ giữ
`configs/semgrep/rulesets.lock`: tên bộ, URL, ngày tải, sha256, số luật. Pipeline từ chối
chạy nếu file luật có tên trong lock mà thiếu hoặc lệch mã băm.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from pr_triage.core.errors import ScanError

DEFAULT_LOCK = "configs/semgrep/rulesets.lock"
FETCH_HINT = "chạy: python scripts/fetch_semgrep_rules.py"


@dataclass(frozen=True)
class Ruleset:
    name: str
    url: str
    file: str
    fetched: str
    sha256: str
    rules: int
    languages: tuple[str, ...] = ()
    semgrep: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["languages"] = list(self.languages)
        return d


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_lock(path: Path) -> dict[str, Ruleset]:
    """Đọc lock, khóa theo tên bộ. Không có file thì trả rỗng."""
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text("utf-8")) or {}
    out: dict[str, Ruleset] = {}
    for name, d in (raw.get("rulesets") or {}).items():
        out[name] = Ruleset(
            name=name,
            url=str(d["url"]),
            file=str(d["file"]),
            fetched=str(d["fetched"]),
            sha256=str(d["sha256"]),
            rules=int(d["rules"]),
            languages=tuple(d.get("languages") or ()),
            semgrep=str(d.get("semgrep") or ""),
        )
    return out


def dump_lock(path: Path, rulesets: Iterable[Ruleset]) -> None:
    body = {
        "version": 1,
        "rulesets": {
            r.name: {k: v for k, v in r.to_dict().items() if k != "name"}
            for r in sorted(rulesets, key=lambda r: r.name)
        },
    }
    header = (
        "# Khóa bộ luật Semgrep (ADR 0015). Chỉ chứa mã băm, KHÔNG chứa luật.\n"
        "# Sửa bằng scripts/fetch_semgrep_rules.py, không sửa tay.\n"
    )
    path.write_text(header + yaml.safe_dump(body, sort_keys=False, allow_unicode=True), "utf-8")


def count_rules(text: str) -> int:
    data = yaml.safe_load(text) or {}
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list) or not rules:
        raise ScanError("file luật không có danh sách `rules`")
    return len(rules)


def filter_languages(text: str, languages: Sequence[str]) -> str:
    """Giữ luật có ít nhất một ngôn ngữ trong danh sách (so không phân biệt hoa thường)."""
    wanted = {lang.lower() for lang in languages}
    data = yaml.safe_load(text)
    kept = [
        r
        for r in data.get("rules", [])
        if wanted & {str(lang).lower() for lang in r.get("languages", [])}
    ]
    if not kept:
        raise ScanError(f"không còn luật nào cho ngôn ngữ {sorted(wanted)}")
    return yaml.safe_dump({"rules": kept}, sort_keys=False, allow_unicode=True)


def verify_rules(rule_paths: Sequence[str], lock_path: Path) -> list[Ruleset]:
    """Kiểm tra mọi file luật có tên trong lock. File luật tự viết (không có trong lock) bỏ qua."""
    by_file = {Path(r.file).name: r for r in load_lock(lock_path).values()}
    checked: list[Ruleset] = []
    for rp in rule_paths:
        entry = by_file.get(Path(rp).name)
        if entry is None:
            continue
        p = Path(rp)
        if not p.is_file():
            raise ScanError(f"thiếu bộ luật {entry.name} ở {rp}; {FETCH_HINT}")
        got = sha256_bytes(p.read_bytes())
        if got != entry.sha256:
            raise ScanError(
                f"bộ luật {entry.name} lệch mã băm trong {lock_path} "
                f"(lock {entry.sha256[:12]}, file {got[:12]}); {FETCH_HINT} --verify để xem, "
                "hoặc tải lại đúng bản đã khóa"
            )
        checked.append(entry)
    return checked
