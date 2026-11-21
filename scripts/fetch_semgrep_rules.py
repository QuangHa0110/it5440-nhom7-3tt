"""Tải bộ luật Semgrep từ registry vào data/rules/ và ghi mã băm vào lock (ADR 0019).

File luật KHÔNG được commit (Semgrep Rules License không cho phân phối lại). Chạy script này
trong hạ tầng nơi bot chạy: máy dev, image Jenkins của công ty.

Tải và khóa (lần đầu, hoặc khi cố ý đổi bộ luật):   python scripts/fetch_semgrep_rules.py
Chỉ giữ luật của vài ngôn ngữ:                      python scripts/fetch_semgrep_rules.py --languages java,kotlin
Tải lại đúng bản đã khóa, lệch thì lỗi (CI, image):  python scripts/fetch_semgrep_rules.py --frozen
Kiểm tra file hiện có khớp lock, không tải:          python scripts/fetch_semgrep_rules.py --verify
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

import httpx

from pr_triage.core.errors import ScanError
from pr_triage.scan.rulesets import (
    DEFAULT_LOCK,
    Ruleset,
    count_rules,
    dump_lock,
    filter_languages,
    load_lock,
    sha256_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
URL = "https://semgrep.dev/c/p/{name}"


def download(url: str, transport: httpx.BaseTransport | None = None) -> str:
    with httpx.Client(timeout=120, follow_redirects=True, transport=transport) as c:
        resp = c.get(url, headers={"Accept": "application/x-yaml, text/yaml, */*"})
    if resp.status_code != 200:
        raise ScanError(f"tải {url} lỗi: HTTP {resp.status_code}")
    return resp.text


def semgrep_version() -> str:
    exe = Path(sys.executable).parent / "semgrep"
    cmd = str(exe) if exe.exists() else shutil.which("semgrep")
    if not cmd:
        return ""
    try:
        out = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""


def fetch(
    name: str,
    root: Path,
    lock_path: Path,
    languages: list[str],
    frozen: bool = False,
    transport: httpx.BaseTransport | None = None,
    today: str | None = None,
) -> Ruleset:
    url = URL.format(name=name)
    locked = load_lock(lock_path).get(name)
    if frozen and locked is not None and not languages:
        languages = list(locked.languages)
    text = download(url, transport)
    count_rules(text)
    if languages:
        text = filter_languages(text, languages)
    data = text.encode("utf-8")
    digest = sha256_bytes(data)
    if frozen:
        if locked is None:
            raise ScanError(f"--frozen nhưng lock chưa có bộ {name}")
        if locked.sha256 != digest:
            raise ScanError(
                f"registry đã đổi bộ {name} (lock {locked.sha256[:12]}, mới {digest[:12]}); "
                "chạy lại không có --frozen nếu cố ý cập nhật, rồi commit lock"
            )
    rel = f"data/rules/semgrep-{name}.yml"
    out = root / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    if frozen and locked is not None:
        return locked
    entry = Ruleset(
        name=name,
        url=url,
        file=rel,
        fetched=today or dt.date.today().isoformat(),
        sha256=digest,
        rules=count_rules(text),
        languages=tuple(sorted(lang.lower() for lang in languages)),
        semgrep=semgrep_version(),
    )
    others = [r for n, r in load_lock(lock_path).items() if n != name]
    dump_lock(lock_path, [*others, entry])
    return entry


def verify(root: Path, lock_path: Path) -> list[str]:
    problems: list[str] = []
    lock = load_lock(lock_path)
    if not lock:
        problems.append(f"{lock_path} rỗng hoặc không có")
    for r in lock.values():
        p = root / r.file
        if not p.is_file():
            problems.append(f"{r.name}: thiếu {r.file}")
        elif sha256_bytes(p.read_bytes()) != r.sha256:
            problems.append(f"{r.name}: {r.file} lệch mã băm")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--name", default="default", help="tên bộ trong registry, ví dụ default, java")
    ap.add_argument("--languages", default="", help="chỉ giữ luật của các ngôn ngữ này (phẩy)")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--lock", type=Path, default=None)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="chỉ kiểm tra file hiện có")
    mode.add_argument("--frozen", action="store_true", help="tải lại, lệch lock thì lỗi")
    args = ap.parse_args(argv)
    lock_path = args.lock or args.root / DEFAULT_LOCK
    if args.verify:
        problems = verify(args.root, lock_path)
        for p in problems:
            print("LỖI:", p, file=sys.stderr)
        if not problems:
            print("khớp lock:", ", ".join(sorted(load_lock(lock_path))))
        return 1 if problems else 0
    langs = [x.strip() for x in args.languages.split(",") if x.strip()]
    try:
        r = fetch(args.name, args.root, lock_path, langs, frozen=args.frozen)
    except (ScanError, httpx.HTTPError) as exc:
        print("LỖI:", exc, file=sys.stderr)
        return 1
    print(f"{r.name}: {r.rules} luật, sha256 {r.sha256[:16]}…, ghi {r.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
