"""Tóm tắt các file kết quả `pr-triage run`/`replay` thành bảng TSV, mỗi file một dòng.

Cột: số cảnh báo mới (A), nhãn của B và C (likely_true/likely_false/unknown), thời gian chạy,
token và chi phí LLM. Dùng để lọc PR theo cách A và để làm tư liệu cho báo cáo, slide.

    uv run python scripts/summarize_runs.py data/raw/<ma-repo>-run/*/triage-result.json
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

LABELS = ("likely_true", "likely_false", "unknown")


def summarize(path: Path) -> str:
    d = json.loads(path.read_text("utf-8"))["result"]
    count = collections.Counter((v["variant"], v["label"]) for v in d["verdicts"])
    llm = [v for v in d["verdicts"] if v["variant"] in ("B", "C")]
    cells = ["/".join(str(count[(var, lab)]) for lab in LABELS) for var in ("B", "C")]
    tokens = sum(v["tokens_in"] + v["tokens_out"] for v in llm)
    cost = sum(v["cost_usd"] for v in llm)
    run = d["run"]
    return "\t".join(
        [str(path), str(run["pr_number"]), str(len(d["findings"])), *cells,
         str(run["duration_s"]), str(tokens), f"{cost:.4f}"]
    )  # fmt: skip


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    print(
        "file\tpr\tA_moi\tB_true/false/unknown\tC_true/false/unknown\tthoi_gian_s\ttoken\tchi_phi_usd"
    )
    for arg in argv:
        print(summarize(Path(arg)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
