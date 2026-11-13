"""Chạy đầu cuối: repo Java thử, thêm một lỗ hổng SQL injection, quét, trích ngữ cảnh, hỏi LLM thật.

Cần PR_TRIAGE_LLM_API_KEY và PR_TRIAGE_LLM_MODEL (biến môi trường hoặc .env). Không chạy trong CI.
Dùng mã nguồn mở và mã mẫu công khai, không dùng mã của công ty Z.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pr_triage import cli  # noqa: E402

VULN = """
    public String search(HttpServletRequest request, java.sql.Statement stmt) throws Exception {
        String name = request.getParameter("name");
        String q = "SELECT * FROM users WHERE name = '" + name + "'";
        return stmt.executeQuery(q).toString();
    }
}
"""


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=e2e@example.org", "-c", "user.name=e2e", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def main() -> int:
    cli.load_dotenv(ROOT / ".env")
    os.environ.setdefault("PR_TRIAGE_LLM_ALLOW_EXTERNAL", "1")
    for var in ("PR_TRIAGE_LLM_API_KEY", "PR_TRIAGE_LLM_MODEL"):
        if not os.environ.get(var):
            print(f"thiếu biến môi trường {var}", file=sys.stderr)
            return 2
    work = Path(tempfile.mkdtemp(prefix="pr-triage-e2e-"))
    try:
        repo = work / "repo"
        shutil.copytree(ROOT / "tests/fixtures/sample_java/src", repo / "src")
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "base")
        git(repo, "switch", "-qc", "feature")
        controller = repo / "src/app/OrderController.java"
        controller.write_text(controller.read_text().rstrip().rstrip("}") + VULN)
        git(repo, "commit", "-qam", "thêm tìm kiếm theo tên")
        out = work / "out"
        os.chdir(ROOT)
        code = cli.main(
            [
                "run",
                "--repo",
                str(repo),
                "--base",
                "main",
                "--head",
                "feature",
                "--pr",
                "1",
                "--db",
                str(work / "store.sqlite"),
                "--out",
                str(out),
                "--repo-alias",
                "e2e",
            ]
        )
        result = json.loads((out / "triage-result.json").read_text("utf-8"))["result"]
        verdicts = result["verdicts"]
        by_variant = {v["variant"]: v for v in verdicts}
        print(
            json.dumps(
                {
                    "findings": [f["finding_id"] for f in result["findings"]],
                    "labels": {k: v["label"] for k, v in by_variant.items()},
                    "explanation_C": by_variant.get("C", {}).get("explanation", ""),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        ok = (
            code == 0
            and len(result["findings"]) >= 1
            and {"A", "B", "C"} <= set(by_variant)
            and all(not v["error"] for v in verdicts)
        )
        print("E2E", "OK" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
