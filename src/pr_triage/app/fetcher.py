"""Lấy mã của PR bằng `git fetch` theo SHA, chỉ đọc (ADR 0012 D3), token không vào argv."""

from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from pr_triage.core.errors import ScmError


class GitFetcher:
    def __init__(
        self, url_template: str = "https://github.com/{repo}.git", timeout_s: int = 300
    ) -> None:
        self._template = url_template
        self._timeout = timeout_s

    @staticmethod
    def _env(token: str, url: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        if url.startswith("http") and token:
            basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
            env.update(
                GIT_CONFIG_COUNT="1",
                GIT_CONFIG_KEY_0="http.extraheader",
                GIT_CONFIG_VALUE_0=f"Authorization: Basic {basic}",
            )
        return env

    def _git(self, cwd: Path, env: dict[str, str], token: str, *args: str) -> bool:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, env=env, capture_output=True, text=True,
            timeout=self._timeout, check=False,
        )  # fmt: skip
        if proc.returncode != 0:
            err = proc.stderr.replace(token, "***") if token else proc.stderr
            self.last_error = err[-300:]
        return proc.returncode == 0

    last_error = ""

    @contextmanager
    def checkout(
        self,
        repo: str,
        token: str,
        shas: Sequence[str],
        pr_number: int,
        optional_shas: Sequence[str] = (),
    ) -> Iterator[Path]:
        """Cấp một kho git tạm chứa các commit cần thiết. `optional_shas` lỗi thì bỏ qua."""
        url = self._template.format(repo=repo)
        env = self._env(token, url)
        with tempfile.TemporaryDirectory(prefix="pr-triage-fetch-") as tmp:
            path = Path(tmp) / "repo"
            path.mkdir()

            def run(*a: str) -> bool:
                return self._git(path, env, token, *a)

            run("init", "-q")
            run("remote", "add", "origin", url)
            for i, sha in enumerate(shas):
                ok = run("fetch", "-q", "--depth=1", "--no-tags", "origin", sha)
                if not ok and i == len(shas) - 1:
                    ok = run(
                        "fetch",
                        "-q",
                        "--depth=1",
                        "--no-tags",
                        "origin",
                        f"refs/pull/{pr_number}/head",
                    )
                if not ok or not run("cat-file", "-e", f"{sha}^{{commit}}"):
                    raise ScmError(f"không lấy được commit {sha[:8]} của {repo}: {self.last_error}")
            for sha in optional_shas:
                run("fetch", "-q", "--depth=1", "--no-tags", "origin", sha)
            yield path
