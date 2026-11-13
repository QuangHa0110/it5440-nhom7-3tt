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

from tests.fakes import FakeScm  # noqa: E402

from pr_triage import cli  # noqa: E402
from pr_triage.bot import FeedbackCollector, Publisher, render, resolve_states  # noqa: E402
from pr_triage.core.alias import Aliaser  # noqa: E402
from pr_triage.core.models import PrRef, Reply  # noqa: E402
from pr_triage.pipeline import result_io  # noqa: E402
from pr_triage.store import SqlStore  # noqa: E402

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
                "--mode",
                "comment",
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
        res = result_io.read(out / "triage-result.json")
        store = SqlStore(work / "store.sqlite")
        scm = FakeScm()
        pr = PrRef("e2e/repo", 1, res.run.head_sha, res.run.base_sha)
        ref = Publisher(scm, store).publish(res, pr, post=True)
        print("--- comment sẽ đăng ---")
        print(render(res))
        code_ = res.displayed[0].short_code
        scm.replies = [Reply("9", "dev-a", f"fp {code_} thử nghiệm", "2026-11-13T00:00:00Z")]
        FeedbackCollector(scm, store, Aliaser("e2e-salt")).collect(res, pr, ref or "")
        state = resolve_states(res.displayed, store.list_feedback(res.run.run_id))[0].state.value
        print("trạng thái sau phản hồi fp:", state)
        ok = (
            state == "marked_false"
            and len(scm.comments) == 1
            and code == 0
            and len(result["findings"]) >= 1
            and {"A", "B", "C"} <= set(by_variant)
            and all(not v["error"] for v in verdicts)
        )
        if not ok:
            print(
                "chi tiết:",
                {
                    "code": code,
                    "state": state,
                    "comments": len(scm.comments),
                    "variants": sorted(by_variant),
                    "errors": [v["error"] for v in verdicts],
                },
            )
        print("E2E", "OK" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
